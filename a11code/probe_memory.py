import argparse
import json

import torch

from .models import build_model


def parse_args():
    parser = argparse.ArgumentParser(
        description='Probe forward/backward memory for one A11 model.')
    parser.add_argument(
        '--model', choices=['tsn2d', 'r3d18', 'r2plus1d18'], required=True)
    parser.add_argument('--frames', type=int, default=8)
    parser.add_argument('--image-size', type=int, default=112)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--grad-checkpoint', action='store_true')
    parser.add_argument('--no-amp', action='store_true')
    parser.add_argument('--pretrained', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is required.')
    device = torch.device('cuda:0')
    model = build_model(
        args.model,
        num_classes=101,
        pretrained=args.pretrained,
        use_checkpoint=args.grad_checkpoint).to(device)
    model.train()
    videos = torch.randn(
        args.batch_size, args.frames, 3, args.image_size, args.image_size,
        device=device)
    labels = torch.zeros(args.batch_size, dtype=torch.long, device=device)
    optimizer = torch.optim.SGD(model.parameters(), lr=1e-4)
    scaler = torch.cuda.amp.GradScaler(enabled=not args.no_amp)
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    with torch.cuda.amp.autocast(enabled=not args.no_amp):
        logits = model(videos)
        loss = torch.nn.functional.cross_entropy(logits, labels)
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
    result = {
        'model': args.model,
        'frames': args.frames,
        'image_size': args.image_size,
        'batch_size': args.batch_size,
        'grad_checkpoint': args.grad_checkpoint,
        'amp': not args.no_amp,
        'pretrained': args.pretrained,
        'max_memory_allocated_mib': (
            torch.cuda.max_memory_allocated() / (1024**2)),
        'max_memory_reserved_mib': (
            torch.cuda.max_memory_reserved() / (1024**2)),
    }
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
