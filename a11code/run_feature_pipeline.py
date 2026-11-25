import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def parse_args():
    parser = argparse.ArgumentParser(
        description='Run the frozen-backbone UCF101 experiment matrix.')
    parser.add_argument(
        '--suite',
        choices=['main', 'sampling', 'budget', 'all'],
        default='main')
    parser.add_argument('--seeds', nargs='+', type=int, default=[0, 1, 2])
    parser.add_argument('--epochs', type=int, default=80)
    parser.add_argument('--num-workers', type=int, default=0)
    parser.add_argument('--no-pretrained', action='store_true')
    parser.add_argument(
        '--manifest-root',
        type=Path,
        default=PROJECT_ROOT / 'results/data')
    parser.add_argument(
        '--video-root',
        type=Path,
        default=PROJECT_ROOT / 'mmaction2-main/data/ucf101/videos')
    return parser.parse_args()


MAIN_CONFIGS = [
    {
        'name': 'tsn2d_uniform',
        'model': 'tsn2d',
        'sampling': 'uniform',
        'frames': 8,
        'image_size': 64,
        'batch_size': 8,
        'sequence_features': True,
        'probes': ['linear', 'temporal'],
    },
    {
        'name': 'r3d18_uniform',
        'model': 'r3d18',
        'sampling': 'uniform',
        'frames': 8,
        'image_size': 64,
        'batch_size': 8,
        'sequence_features': False,
        'probes': ['linear'],
    },
    {
        'name': 'r2plus1d18_uniform',
        'model': 'r2plus1d18',
        'sampling': 'uniform',
        'frames': 8,
        'image_size': 64,
        'batch_size': 8,
        'sequence_features': False,
        'probes': ['linear'],
    },
]

SAMPLING_CONFIGS = [
    {
        'name': 'tsn2d_dense',
        'model': 'tsn2d',
        'sampling': 'dense',
        'frames': 8,
        'image_size': 64,
        'batch_size': 8,
        'sequence_features': True,
        'probes': ['linear', 'temporal'],
    },
    {
        'name': 'tsn2d_adaptive',
        'model': 'tsn2d',
        'sampling': 'adaptive',
        'frames': 8,
        'image_size': 64,
        'batch_size': 8,
        'sequence_features': True,
        'probes': ['linear', 'temporal'],
    },
]

BUDGET_CONFIGS = [
    {
        'name': 'budget_time_k16_r48',
        'model': 'tsn2d',
        'sampling': 'uniform',
        'frames': 16,
        'image_size': 48,
        'batch_size': 8,
        'sequence_features': True,
        'probes': ['linear', 'temporal'],
    },
    {
        'name': 'budget_space_k4_r112',
        'model': 'tsn2d',
        'sampling': 'uniform',
        'frames': 4,
        'image_size': 112,
        'batch_size': 8,
        'sequence_features': True,
        'probes': ['linear', 'temporal'],
    },
]


def run_command(command, log_path):
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('w', encoding='utf-8') as log:
        log.write(' '.join(map(str, command)) + '\n')
        log.flush()
        process = subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace')
        output = []
        for line in process.stdout:
            print(line, end='')
            log.write(line)
            log.flush()
            output.append(line)
        code = process.wait()
    if code != 0:
        raise RuntimeError(f'Command failed with exit code {code}: {command}')
    return ''.join(output)


def extract(
        config,
        suite_root,
        seed=0,
        num_workers=0,
        manifest_root=None,
        video_root=None,
        no_pretrained=False):
    command = [
        PYTHON, '-X', 'utf8', '-m', 'a11code.extract_features',
        '--model', config['model'],
        '--sampling', config['sampling'],
        '--seed', str(seed),
        '--frames', str(config['frames']),
        '--image-size', str(config['image_size']),
        '--batch-size', str(config['batch_size']),
        '--num-workers', str(num_workers),
        '--output-root', str(suite_root / 'features'),
        '--manifest-root', str(manifest_root),
        '--video-root', str(video_root),
    ]
    if no_pretrained:
        command.append('--no-pretrained')
    if config.get('sequence_features'):
        command.append('--sequence-features')
    output = run_command(
        command, suite_root / 'logs' / f"{config['name']}_extract.log")
    match = re.search(r'Feature output:\s*(.+)', output)
    if not match:
        raise RuntimeError(f"Cannot locate feature output for {config['name']}")
    return Path(match.group(1).strip())


def probe(feature_dir, seed, epochs, suite_root, probe_type):
    module = (
        'a11code.temporal_probe'
        if probe_type == 'temporal'
        else 'a11code.linear_probe')
    probe_root = suite_root / 'probes' / probe_type
    command = [
        PYTHON, '-X', 'utf8', '-m', module,
        '--features-dir', str(feature_dir),
        '--seed', str(seed),
        '--epochs', str(epochs),
        '--output-root', str(probe_root),
    ]
    run_command(
        command,
        suite_root / 'logs' /
        f'{feature_dir.name}_{probe_type}_s{seed}.log')
    return (
        probe_root / f'{feature_dir.name}_s{seed}' / 'metrics.json')


def main():
    args = parse_args()
    suites = []
    if args.suite in {'main', 'all'}:
        suites.append(('main', MAIN_CONFIGS))
    if args.suite in {'sampling', 'all'}:
        suites.append(('sampling', SAMPLING_CONFIGS))
    if args.suite in {'budget', 'all'}:
        suites.append(('budget', BUDGET_CONFIGS))

    run_root = (
        PROJECT_ROOT / 'results' / 'feature_pipeline' /
        f'{args.suite}_{datetime.now():%Y%m%d_%H%M%S}')
    run_root.mkdir(parents=True, exist_ok=False)
    matrix = []
    for suite_name, configs in suites:
        suite_root = run_root / suite_name
        for config in configs:
            print(f"\n=== Extracting {config['name']} ===")
            feature_dir = extract(
                config,
                suite_root,
                num_workers=args.num_workers,
                manifest_root=args.manifest_root,
                video_root=args.video_root,
                no_pretrained=args.no_pretrained)
            feature_metrics = json.loads(
                (feature_dir / 'metrics.json').read_text(encoding='utf-8'))
            for probe_type in config['probes']:
                for seed in args.seeds:
                    print(
                        f"=== Probing {config['name']} "
                        f"{probe_type} seed {seed} ===")
                    metrics_path = probe(
                        feature_dir,
                        seed,
                        args.epochs,
                        suite_root,
                        probe_type)
                    metrics = json.loads(
                        metrics_path.read_text(encoding='utf-8'))
                    matrix.append({
                        'suite': suite_name,
                        'config': config['name'],
                        'probe_type': probe_type,
                        'seed': seed,
                        'feature_dir': str(feature_dir),
                        'metrics_path': str(metrics_path),
                        'top1': metrics['test']['top1'],
                        'top5': metrics['test']['top5'],
                        'max_memory_allocated_mib': metrics[
                            'max_memory_allocated_mib'],
                        'max_memory_reserved_mib': metrics[
                            'max_memory_reserved_mib'],
                        'feature_metrics': feature_metrics['splits'],
                    })
                    (run_root / 'matrix.json').write_text(
                        json.dumps(matrix, ensure_ascii=False, indent=2),
                        encoding='utf-8')
    print(f'Experiment matrix: {run_root}')


if __name__ == '__main__':
    main()
