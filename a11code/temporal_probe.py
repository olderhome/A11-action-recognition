import argparse
import csv
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from .models import TemporalAttentionHead
from .train import seed_everything


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    parser = argparse.ArgumentParser(
        description='Train a temporal attention head on TSN sequence features.')
    parser.add_argument('--features-dir', type=Path, required=True)
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--epochs', type=int, default=60)
    parser.add_argument('--batch-size', type=int, default=256)
    parser.add_argument('--lr', type=float, default=1e-4)
    parser.add_argument('--budget-mib', type=float, default=2048.0)
    parser.add_argument(
        '--output-root',
        type=Path,
        default=PROJECT_ROOT / 'results/temporal_probe')
    return parser.parse_args()


def load_split(directory, split):
    features = np.load(directory / f'{split}_features.npy').astype(np.float32)
    labels = np.load(directory / f'{split}_labels.npy').astype(np.int64)
    with (directory / f'{split}_metadata.csv').open(
            newline='', encoding='utf-8') as handle:
        paths = [row['path'] for row in csv.DictReader(handle)]
    return features, labels, paths


def evaluate(model, features, labels):
    model.eval()
    predictions = []
    with torch.no_grad():
        for start in range(0, len(features), 512):
            predictions.append(model(features[start:start + 512]))
        logits = torch.cat(predictions)
    top5 = logits.topk(5, dim=1).indices
    top1_correct = top5[:, 0].eq(labels)
    top5_correct = top5.eq(labels.unsqueeze(1)).any(dim=1)
    return {
        'top1': float(top1_correct.float().mean()),
        'top5': float(top5_correct.float().mean()),
        'samples': int(labels.numel()),
    }, logits


def main():
    args = parse_args()
    seed_everything(args.seed)
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
    train_x, train_y, _ = load_split(args.features_dir, 'train_fit')
    val_x, val_y, _ = load_split(args.features_dir, 'val')
    test_x, test_y, paths = load_split(args.features_dir, 'test')
    if train_x.ndim != 3:
        raise RuntimeError('Temporal probe requires [N, T, D] features.')
    mean = train_x.mean(axis=(0, 1), keepdims=True)
    std = train_x.std(axis=(0, 1), keepdims=True) + 1e-6
    train_x = torch.from_numpy((train_x - mean) / std).to(device)
    val_x = torch.from_numpy((val_x - mean) / std).to(device)
    test_x = torch.from_numpy((test_x - mean) / std).to(device)
    train_y = torch.from_numpy(train_y).to(device)
    val_y = torch.from_numpy(val_y).to(device)
    test_y = torch.from_numpy(test_y).to(device)

    model = TemporalAttentionHead(
        input_dim=train_x.shape[-1]).to(device)
    if str(device).startswith('cuda'):
        torch.cuda.reset_peak_memory_stats()
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.epochs)
    generator = torch.Generator().manual_seed(args.seed)
    history = []
    best_top1 = -1.0
    best_state = None
    run_dir = args.output_root / (
        f'{args.features_dir.name}_s{args.seed}')
    run_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        order = torch.randperm(len(train_x), generator=generator)
        total_loss = 0.0
        for start in range(0, len(order), args.batch_size):
            indices = order[start:start + args.batch_size].to(device)
            logits = model(train_x[indices])
            loss = F.cross_entropy(logits, train_y[indices])
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            total_loss += float(loss) * len(indices)
        scheduler.step()
        if str(device).startswith('cuda') and (
                torch.cuda.max_memory_reserved() >
                args.budget_mib * 1024**2):
            raise RuntimeError(
                f'Memory budget exceeded: '
                f'{torch.cuda.max_memory_reserved() / 1024**2:.1f} MiB')
        metrics, _ = evaluate(model, val_x, val_y)
        metrics.update({
            'epoch': epoch,
            'train_loss': total_loss / len(train_x),
        })
        history.append(metrics)
        if metrics['top1'] > best_top1:
            best_top1 = metrics['top1']
            best_state = {
                key: value.detach().clone()
                for key, value in model.state_dict().items()
            }

    model.load_state_dict(best_state)
    final, logits = evaluate(model, test_x, test_y)
    probabilities = torch.softmax(logits, dim=1)
    values, indices = probabilities.topk(5, dim=1)
    with (run_dir / 'predictions.csv').open(
            'w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow([
            'path', 'label', 'prediction', 'score',
            'top5_indices', 'top5_scores'])
        writer.writerows(zip(
            paths,
            test_y.cpu().tolist(),
            indices[:, 0].cpu().tolist(),
            values[:, 0].cpu().tolist(),
            ['|'.join(map(str, row)) for row in indices.cpu().tolist()],
            ['|'.join(f'{value:.8f}' for value in row)
             for row in values.cpu().tolist()]))
    result = {
        'source_features': str(args.features_dir),
        'seed': args.seed,
        'epochs': args.epochs,
        'test': final,
        'validation_best_top1': best_top1,
        'max_memory_allocated_mib': (
            torch.cuda.max_memory_allocated() / (1024**2)
            if str(device).startswith('cuda') else 0.0),
        'max_memory_reserved_mib': (
            torch.cuda.max_memory_reserved() / (1024**2)
            if str(device).startswith('cuda') else 0.0),
        'history': history,
    }
    (run_dir / 'metrics.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding='utf-8')
    print(f'Temporal probe output: {run_dir}')


if __name__ == '__main__':
    main()
