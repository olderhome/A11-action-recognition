import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    'tsn_amp': 'TSN AMP',
    'tsn_amp_checkpoint': 'TSN AMP+检查点',
    'tsn_fp32': 'TSN FP32',
    'r3d_amp': 'R3D AMP',
    'r3d_amp_checkpoint': 'R3D AMP+检查点',
    'r2plus_fp32': 'R2+1D FP32',
}


def parse_args():
    parser = argparse.ArgumentParser(
        description='Plot A11 memory ablation results.')
    parser.add_argument('--matrix', type=Path, required=True)
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=PROJECT_ROOT / 'figures')
    return parser.parse_args()


def configure():
    font_path = Path('C:/Windows/Fonts/msyh.ttc')
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        plt.rcParams['font.family'] = 'Microsoft YaHei'
    plt.rcParams.update({
        'axes.unicode_minus': False,
        'font.size': 10,
        'savefig.dpi': 320,
        'savefig.bbox': 'tight',
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'grid.color': '#D8DADC',
        'grid.linewidth': 0.6,
    })


def main():
    args = parse_args()
    configure()
    rows = [
        row for row in json.loads(
            args.matrix.read_text(encoding='utf-8'))
        if row['status'] == 'ok'
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    labels = [LABELS.get(row['name'], row['name']) for row in rows]
    allocated = [row['max_memory_allocated_mib'] for row in rows]
    reserved = [row['max_memory_reserved_mib'] for row in rows]
    x = np.arange(len(rows))
    width = 0.36
    fig, axis = plt.subplots(figsize=(8.8, 4.8), constrained_layout=True)
    axis.bar(
        x - width / 2, allocated, width,
        color='#176F6B', label='allocated')
    axis.bar(
        x + width / 2, reserved, width,
        color='#C46A18', label='reserved')
    axis.axhline(
        2048, color='#B43E3E', linewidth=1.2, linestyle='--',
        label='2 GiB 上限')
    for index, value in enumerate(reserved):
        axis.text(index + width / 2, value + 20, f'{value:.0f}', ha='center')
    axis.set_xticks(x, labels, rotation=25, ha='right')
    axis.set_ylabel('显存 / MiB')
    axis.set_ylim(0, 2250)
    axis.legend(frameon=False, ncol=3)
    axis.grid(axis='x', visible=False)
    fig.savefig(args.output_dir / 'memory_efficiency.pdf')
    fig.savefig(args.output_dir / 'memory_efficiency.png')
    plt.close(fig)

    with (args.output_dir / 'memory_efficiency_data.csv').open(
            'w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow([
            'experiment', 'model', 'batch_size',
            'allocated_mib', 'reserved_mib'])
        for row in rows:
            writer.writerow([
                row['name'], row['model'], row['batch_size'],
                row['max_memory_allocated_mib'],
                row['max_memory_reserved_mib']])
    print(f'Memory figure: {args.output_dir}')


if __name__ == '__main__':
    main()
