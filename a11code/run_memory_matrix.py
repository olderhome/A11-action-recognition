import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


CONFIGS = [
    {
        'name': 'tsn_amp',
        'model': 'tsn2d',
        'frames': 8,
        'image_size': 64,
        'batch_size': 8,
        'extra': [],
    },
    {
        'name': 'tsn_amp_checkpoint',
        'model': 'tsn2d',
        'frames': 8,
        'image_size': 64,
        'batch_size': 8,
        'extra': ['--grad-checkpoint'],
    },
    {
        'name': 'tsn_fp32',
        'model': 'tsn2d',
        'frames': 8,
        'image_size': 64,
        'batch_size': 8,
        'extra': ['--no-amp'],
    },
    {
        'name': 'r3d_amp',
        'model': 'r3d18',
        'frames': 8,
        'image_size': 64,
        'batch_size': 8,
        'extra': [],
    },
    {
        'name': 'r3d_amp_checkpoint',
        'model': 'r3d18',
        'frames': 8,
        'image_size': 64,
        'batch_size': 8,
        'extra': ['--grad-checkpoint'],
    },
    {
        'name': 'r2plus_fp32',
        'model': 'r2plus1d18',
        'frames': 8,
        'image_size': 64,
        'batch_size': 2,
        'extra': ['--no-amp'],
    },
]


def parse_args():
    parser = argparse.ArgumentParser(
        description='Measure AMP/checkpoint memory variants.')
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = args.output_dir or (
        PROJECT_ROOT / 'results' / 'memory' /
        f'memory_{datetime.now():%Y%m%d_%H%M%S}')
    output_dir.mkdir(parents=True, exist_ok=False)
    rows = []
    for config in CONFIGS:
        command = [
            PYTHON, '-X', 'utf8', '-m', 'a11code.probe_memory',
            '--model', config['model'],
            '--frames', str(config['frames']),
            '--image-size', str(config['image_size']),
            '--batch-size', str(config['batch_size']),
            *config['extra'],
        ]
        print(f"=== {config['name']} ===")
        process = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace')
        (output_dir / f"{config['name']}.log").write_text(
            process.stdout + process.stderr, encoding='utf-8')
        if process.returncode != 0:
            rows.append({
                **config,
                'status': 'failed',
                'error': process.stderr[-2000:],
            })
        else:
            result = json.loads(process.stdout)
            rows.append({**config, 'status': 'ok', **result})
        (output_dir / 'matrix.json').write_text(
            json.dumps(rows, ensure_ascii=False, indent=2),
            encoding='utf-8')
    print(f'Memory matrix: {output_dir}')


if __name__ == '__main__':
    main()
