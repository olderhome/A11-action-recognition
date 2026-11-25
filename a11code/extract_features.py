import argparse
import csv
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from .data import UCFVideoDataset, collate_video_batch
from .models import build_model
from .sampling import build_sampler
from .train import seed_everything


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    parser = argparse.ArgumentParser(
        description='Extract frozen video features for UCF101.')
    parser.add_argument(
        '--model', choices=['tsn2d', 'r3d18', 'r2plus1d18'], required=True)
    parser.add_argument(
        '--sampling',
        choices=['uniform', 'dense', 'adaptive'],
        default='uniform')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--frames', type=int, default=8)
    parser.add_argument('--image-size', type=int, default=64)
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--num-workers', type=int, default=0)
    parser.add_argument('--train-limit', type=int, default=0)
    parser.add_argument('--test-limit', type=int, default=0)
    parser.add_argument('--grad-checkpoint', action='store_true')
    parser.add_argument('--no-pretrained', action='store_true')
    parser.add_argument('--sequence-features', action='store_true')
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
        default=PROJECT_ROOT / 'results/features')
    return parser.parse_args()


def extract(model, loader, device, sequence_features=False):
    model.eval()
    features = []
    labels = []
    paths = []
    decode_seconds = 0.0
    start = time.perf_counter()
    with torch.no_grad():
        for batch in loader:
            videos = batch['video'].to(device, non_blocking=True)
            with torch.cuda.amp.autocast(enabled=True):
                if sequence_features:
                    value = model.sequence_features(videos)
                else:
                    value = model.features(videos)
            features.append(value.float().cpu().half())
            labels.extend(batch['label'].tolist())
            paths.extend(batch['path'])
            decode_seconds += float(batch['decode_seconds'].sum())
    elapsed = time.perf_counter() - start
    return (
        torch.cat(features).numpy(),
        np.asarray(labels, dtype=np.int64),
        paths,
        {
            'samples': len(labels),
            'elapsed_seconds': elapsed,
            'throughput_videos_per_second': len(labels) / max(elapsed, 1e-9),
            'decode_seconds': decode_seconds,
            'max_memory_allocated_mib': (
                torch.cuda.max_memory_allocated() / (1024**2)),
            'max_memory_reserved_mib': (
                torch.cuda.max_memory_reserved() / (1024**2)),
        })


def write_metadata(path, row_paths, labels):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['path', 'label'])
        writer.writerows(zip(row_paths, labels.tolist()))


def main():
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is required.')
    seed_everything(args.seed)
    device = torch.device('cuda:0')
    manifest = args.manifest_root / 'ucf101_split1'
    run_name = (
        f'{args.model}_{args.sampling}_s{args.seed}_f{args.frames}'
        f'_r{args.image_size}_{datetime.now():%Y%m%d_%H%M%S}')
    run_dir = args.output_root / run_name
    run_dir.mkdir(parents=True, exist_ok=False)

    model = build_model(
        args.model,
        pretrained=not args.no_pretrained,
        use_checkpoint=args.grad_checkpoint).to(device)
    normalization = (
        'kinetics' if args.model in {'r3d18', 'r2plus1d18'}
        else 'imagenet')
    results = {}
    for split, training, limit in [
            ('train_fit', True, args.train_limit),
            ('val', False, args.test_limit),
            ('test', False, args.test_limit)]:
        dataset = UCFVideoDataset(
            f'{manifest}_{split}.csv',
            args.video_root,
            build_sampler(args.sampling),
            num_frames=args.frames,
            image_size=args.image_size,
            training=training,
            limit=limit,
            seed=args.seed,
            normalization=normalization)
        loader = DataLoader(
            dataset,
            batch_size=args.batch_size,
            shuffle=False,
            num_workers=args.num_workers,
            pin_memory=True,
            collate_fn=collate_video_batch)
        if args.sequence_features and args.model != 'tsn2d':
            raise ValueError('Sequence features are only available for TSN.')
        features, labels, paths, metrics = extract(
            model, loader, device, args.sequence_features)
        np.save(run_dir / f'{split}_features.npy', features)
        np.save(run_dir / f'{split}_labels.npy', labels)
        write_metadata(run_dir / f'{split}_metadata.csv', paths, labels)
        results[split] = metrics

    config = vars(args).copy()
    config.update({
        'run_name': run_name,
        'feature_dim': int(features.shape[-1]),
        'feature_dtype': 'float16',
        'sequence_features': args.sequence_features,
    })
    (run_dir / 'metrics.json').write_text(
        json.dumps(
            {
                'config': {
                    key: str(value) if isinstance(value, Path) else value
                    for key, value in config.items()
                },
                'splits': results,
            },
            ensure_ascii=False,
            indent=2),
        encoding='utf-8')
    print(f'Feature output: {run_dir}')


if __name__ == '__main__':
    main()

