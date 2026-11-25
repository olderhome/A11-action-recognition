import argparse
import csv
import json
import math
import random
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from .data import UCFVideoDataset, collate_video_batch
from .models import build_model
from .sampling import build_sampler


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    parser = argparse.ArgumentParser(
        description='Train an A11 UCF101 model under a memory budget.')
    parser.add_argument(
        '--model',
        choices=['tsn2d', 'r3d18', 'r2plus1d18'],
        required=True)
    parser.add_argument(
        '--sampling',
        choices=['uniform', 'dense', 'adaptive'],
        default='uniform')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--epochs', type=int, default=12)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--grad-accum', type=int, default=8)
    parser.add_argument('--frames', type=int, default=8)
    parser.add_argument('--image-size', type=int, default=112)
    parser.add_argument('--lr', type=float, default=5e-4)
    parser.add_argument('--weight-decay', type=float, default=1e-4)
    parser.add_argument('--num-workers', type=int, default=0)
    parser.add_argument('--val-every', type=int, default=1)
    parser.add_argument('--train-limit', type=int, default=0)
    parser.add_argument('--val-limit', type=int, default=0)
    parser.add_argument('--budget-mib', type=float, default=2048.0)
    parser.add_argument('--grad-checkpoint', action='store_true')
    parser.add_argument('--no-amp', action='store_true')
    parser.add_argument('--no-pretrained', action='store_true')
    parser.add_argument(
        '--manifest-root',
        type=Path,
        default=PROJECT_ROOT / 'results/data')
    parser.add_argument(
        '--video-root',
        type=Path,
        default=PROJECT_ROOT / 'mmaction2-main/data/ucf101/videos')
    parser.add_argument(
        '--output-root',
        type=Path,
        default=PROJECT_ROOT / 'results/runs')
    parser.add_argument('--tag', default='')
    return parser.parse_args()


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = False


def make_loader(dataset, batch_size, shuffle, num_workers):
    generator = torch.Generator()
    generator.manual_seed(dataset.seed)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=True,
        persistent_workers=num_workers > 0,
        collate_fn=collate_video_batch,
        generator=generator)


def accuracy(logits, labels):
    top5 = logits.topk(min(5, logits.shape[1]), dim=1).indices
    top1_correct = top5[:, 0].eq(labels)
    top5_correct = top5.eq(labels.unsqueeze(1)).any(dim=1)
    return top1_correct, top5_correct


def evaluate(model, loader, device, amp):
    model.eval()
    total = 0
    top1 = 0
    top5 = 0
    loss_sum = 0.0
    decode_seconds = 0.0
    score_cost = 0.0
    rows = []
    start = time.perf_counter()
    with torch.no_grad():
        for batch in loader:
            videos = batch['video'].to(device, non_blocking=True)
            labels = batch['label'].to(device, non_blocking=True)
            with torch.cuda.amp.autocast(enabled=amp):
                logits = model(videos)
                loss = F.cross_entropy(logits, labels)
            correct1, correct5 = accuracy(logits, labels)
            probabilities = torch.softmax(logits.float(), dim=1)
            values, indices = probabilities.topk(5, dim=1)
            total += labels.numel()
            top1 += int(correct1.sum())
            top5 += int(correct5.sum())
            loss_sum += float(loss) * labels.numel()
            decode_seconds += float(batch['decode_seconds'].sum())
            score_cost += float(batch['score_cost'].sum())
            for path, label, prediction, score, top_indices, top_values in zip(
                    batch['path'],
                    labels.cpu().tolist(),
                    indices[:, 0].cpu().tolist(),
                    values[:, 0].cpu().tolist(),
                    indices.cpu().tolist(),
                    values.cpu().tolist()):
                rows.append({
                    'path': path,
                    'label': label,
                    'prediction': prediction,
                    'score': score,
                    'top5_indices': '|'.join(map(str, top_indices)),
                    'top5_scores': '|'.join(
                        f'{value:.8f}' for value in top_values),
                })
    elapsed = time.perf_counter() - start
    return {
        'loss': loss_sum / max(total, 1),
        'top1': top1 / max(total, 1),
        'top5': top5 / max(total, 1),
        'samples': total,
        'elapsed_seconds': elapsed,
        'throughput_videos_per_second': total / max(elapsed, 1e-9),
        'decode_seconds': decode_seconds,
        'adaptive_score_cost': score_cost,
        'max_memory_allocated_mib': (
            torch.cuda.max_memory_allocated() / (1024**2)),
        'max_memory_reserved_mib': (
            torch.cuda.max_memory_reserved() / (1024**2)),
    }, rows


def main():
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is required for the memory-budget experiment.')
    seed_everything(args.seed)
    torch.cuda.empty_cache()
    device = torch.device('cuda:0')
    amp = not args.no_amp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_name = (
        f'{args.model}_{args.sampling}_s{args.seed}_{timestamp}')
    if args.tag:
        run_name = f'{args.tag}_{run_name}'
    run_dir = args.output_root / run_name
    run_dir.mkdir(parents=True, exist_ok=False)

    manifest_prefix = args.manifest_root / 'ucf101_split1'
    sampler = build_sampler(args.sampling)
    normalization = (
        'kinetics' if args.model in {'r3d18', 'r2plus1d18'}
        else 'imagenet')
    train_dataset = UCFVideoDataset(
        f'{manifest_prefix}_train_fit.csv',
        args.video_root,
        sampler,
        num_frames=args.frames,
        image_size=args.image_size,
        training=True,
        limit=args.train_limit,
        seed=args.seed,
        normalization=normalization)
    val_dataset = UCFVideoDataset(
        f'{manifest_prefix}_val.csv',
        args.video_root,
        build_sampler(args.sampling),
        num_frames=args.frames,
        image_size=args.image_size,
        training=False,
        limit=args.val_limit,
        seed=args.seed + 10000,
        normalization=normalization)
    test_dataset = UCFVideoDataset(
        f'{manifest_prefix}_test.csv',
        args.video_root,
        build_sampler(args.sampling),
        num_frames=args.frames,
        image_size=args.image_size,
        training=False,
        limit=args.val_limit,
        seed=args.seed + 20000,
        normalization=normalization)

    train_loader = make_loader(
        train_dataset, args.batch_size, True, args.num_workers)
    val_loader = make_loader(
        val_dataset, args.batch_size, False, args.num_workers)
    test_loader = make_loader(
        test_dataset, args.batch_size, False, args.num_workers)
    model = build_model(
        args.model,
        num_classes=101,
        pretrained=not args.no_pretrained,
        use_checkpoint=args.grad_checkpoint).to(device)

    optimizer = torch.optim.SGD(
        model.parameters(),
        lr=args.lr,
        momentum=0.9,
        weight_decay=args.weight_decay,
        nesterov=True)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=max(args.epochs, 1), eta_min=args.lr * 0.01)
    scaler = torch.cuda.amp.GradScaler(enabled=amp)

    config = vars(args).copy()
    config.update({
        'run_name': run_name,
        'train_samples': len(train_dataset),
        'validation_samples': len(val_dataset),
        'test_samples': len(test_dataset),
        'effective_batch_size': args.batch_size * args.grad_accum,
        'amp': amp,
        'device': str(device),
    })
    (run_dir / 'config.json').write_text(
        json.dumps(
            {
                key: str(value) if isinstance(value, Path) else value
                for key, value in config.items()
            },
            ensure_ascii=False,
            indent=2),
        encoding='utf-8')

    best_top1 = -1.0
    history = []
    global_start = time.perf_counter()
    for epoch in range(1, args.epochs + 1):
        train_dataset.set_epoch(epoch)
        model.train()
        optimizer.zero_grad(set_to_none=True)
        torch.cuda.reset_peak_memory_stats()
        epoch_start = time.perf_counter()
        loss_sum = 0.0
        train_samples = 0
        decode_seconds = 0.0
        for step, batch in enumerate(train_loader, start=1):
            videos = batch['video'].to(device, non_blocking=True)
            labels = batch['label'].to(device, non_blocking=True)
            with torch.cuda.amp.autocast(enabled=amp):
                logits = model(videos)
                loss = F.cross_entropy(logits, labels)
            scaled_loss = loss / args.grad_accum
            scaler.scale(scaled_loss).backward()
            loss_sum += float(loss) * labels.numel()
            train_samples += labels.numel()
            decode_seconds += float(batch['decode_seconds'].sum())
            if step % args.grad_accum == 0:
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
            if torch.cuda.max_memory_reserved() > (
                    args.budget_mib * 1024**2):
                raise RuntimeError(
                    f'Memory budget exceeded at epoch {epoch}, step {step}: '
                    f'{torch.cuda.max_memory_reserved() / 1024**2:.1f} MiB')
        if len(train_loader) % args.grad_accum != 0:
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)

        train_epoch_seconds = time.perf_counter() - epoch_start
        epoch_record = {
            'epoch': epoch,
            'lr': scheduler.get_last_lr()[0],
            'train_loss': loss_sum / max(train_samples, 1),
            'train_samples': train_samples,
            'train_elapsed_seconds': train_epoch_seconds,
            'train_throughput_videos_per_second': (
                train_samples / max(train_epoch_seconds, 1e-9)),
            'decode_seconds': decode_seconds,
            'train_max_memory_allocated_mib': (
                torch.cuda.max_memory_allocated() / (1024**2)),
            'train_max_memory_reserved_mib': (
                torch.cuda.max_memory_reserved() / (1024**2)),
        }
        if epoch % args.val_every == 0 or epoch == args.epochs:
            validation, _ = evaluate(model, val_loader, device, amp)
            epoch_record['validation'] = validation
            if validation['top1'] > best_top1:
                best_top1 = validation['top1']
                torch.save({
                    'model': model.state_dict(),
                    'epoch': epoch,
                    'top1': validation['top1'],
                    'config': config,
                }, run_dir / 'best.pth')
        scheduler.step()
        history.append(epoch_record)
        (run_dir / 'history.json').write_text(
            json.dumps(history, ensure_ascii=False, indent=2),
            encoding='utf-8')
        print(json.dumps(epoch_record, ensure_ascii=False))

    checkpoint = torch.load(
        run_dir / 'best.pth', map_location=device)
    model.load_state_dict(checkpoint['model'])
    final_metrics, prediction_rows = evaluate(
        model, test_loader, device, amp)
    with (run_dir / 'predictions.csv').open(
            'w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(prediction_rows[0].keys()))
        writer.writeheader()
        writer.writerows(prediction_rows)
    final_metrics.update({
        'best_epoch': checkpoint['epoch'],
        'best_validation_top1': checkpoint['top1'],
        'run_elapsed_seconds': time.perf_counter() - global_start,
        'parameters': sum(
            parameter.numel() for parameter in model.parameters()),
        'parameter_mib': sum(
            parameter.numel() * parameter.element_size()
            for parameter in model.parameters()) / (1024**2),
    })
    (run_dir / 'metrics.json').write_text(
        json.dumps(final_metrics, ensure_ascii=False, indent=2),
        encoding='utf-8')
    print(f'Run output: {run_dir}')


if __name__ == '__main__':
    main()
