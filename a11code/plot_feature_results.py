import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    'tsn2d_uniform': 'TSN-2D',
    'r3d18_uniform': 'R3D-18',
    'r2plus1d18_uniform': 'R(2+1)D-18',
    'tsn2d_dense': 'TSN-密集',
    'tsn2d_adaptive': 'TSN-自适应',
    'budget_time_k16_r48': '时间优先',
    'budget_space_k4_r112': '空间优先',
}
COLORS = {
    'main': '#176F6B',
    'sampling': '#C46A18',
    'budget': '#6A5AA8',
}


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


def parse_args():
    parser = argparse.ArgumentParser(
        description='Create paper figures from frozen feature experiments.')
    parser.add_argument('--matrix', type=Path, required=True)
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=PROJECT_ROOT / 'figures')
    return parser.parse_args()


def summarize(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[
            (row['suite'], row['config'], row['probe_type'])
        ].append(row)
    summary = []
    for (suite, config, probe_type), values in groups.items():
        top1 = [item['top1'] for item in values]
        top5 = [item['top5'] for item in values]
        test_metrics = values[0]['feature_metrics']['test']
        summary.append({
            'suite': suite,
            'config': config,
            'probe_type': probe_type,
            'label': (
                LABELS.get(config, config) +
                ('·时序' if probe_type == 'temporal' else '·线性')),
            'seed_count': len(values),
            'top1_mean': statistics.mean(top1),
            'top1_std': (
                statistics.stdev(top1) if len(top1) > 1 else 0.0),
            'top5_mean': statistics.mean(top5),
            'top5_std': (
                statistics.stdev(top5) if len(top5) > 1 else 0.0),
            'feature_throughput': test_metrics[
                'throughput_videos_per_second'],
            'feature_peak_mib': test_metrics[
                'max_memory_reserved_mib'],
        })
    return summary


def save(fig, output_dir, name):
    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / f'{name}.pdf')
    fig.savefig(output_dir / f'{name}.png')
    plt.close(fig)


def plot_main(summary, output_dir):
    rows = [item for item in summary if item['suite'] == 'main']
    if not rows:
        return
    x = np.arange(len(rows))
    width = 0.36
    fig, axis = plt.subplots(figsize=(7.4, 4.5), constrained_layout=True)
    axis.bar(
        x - width / 2,
        [item['top1_mean'] * 100 for item in rows],
        width,
        yerr=[item['top1_std'] * 100 for item in rows],
        capsize=3,
        color='#176F6B',
        label='Top-1')
    axis.bar(
        x + width / 2,
        [item['top5_mean'] * 100 for item in rows],
        width,
        yerr=[item['top5_std'] * 100 for item in rows],
        capsize=3,
        color='#C46A18',
        label='Top-5')
    for index, item in enumerate(rows):
        axis.text(
            index - width / 2, item['top1_mean'] * 100 + 1.5,
            f"{item['top1_mean'] * 100:.1f}", ha='center', fontsize=8)
        axis.text(
            index + width / 2, item['top5_mean'] * 100 + 1.5,
            f"{item['top5_mean'] * 100:.1f}", ha='center', fontsize=8)
    axis.set_xticks(x, [item['label'] for item in rows])
    axis.set_ylabel('准确率 / %')
    axis.set_ylim(0, 100)
    axis.legend(frameon=False, ncol=2)
    axis.grid(axis='x', visible=False)
    save(fig, output_dir, 'main_route_accuracy')


def plot_seed_variation(rows, output_dir):
    main_rows = [row for row in rows if row['suite'] == 'main']
    if not main_rows:
        return
    groups = []
    for row in main_rows:
        key = (row['config'], row['probe_type'])
        if key not in groups:
            groups.append(key)
    fig, axis = plt.subplots(figsize=(7.2, 4.2), constrained_layout=True)
    for offset, (config, probe_type) in enumerate(groups):
        values = [
            row['top1'] * 100 for row in main_rows
            if row['config'] == config and row['probe_type'] == probe_type
        ]
        x = np.full(len(values), offset, dtype=float)
        axis.scatter(x, values, s=45, color='#176F6B')
        axis.hlines(
            statistics.mean(values), offset - 0.15, offset + 0.15,
            color='#3D4448', linewidth=1)
    axis.set_xticks(
        range(len(groups)),
        [
            LABELS.get(config, config) +
            ('·时序' if probe_type == 'temporal' else '·线性')
            for config, probe_type in groups
        ],
        rotation=20,
        ha='right')
    axis.set_ylabel('Top-1 / %')
    axis.set_ylim(0, 100)
    axis.grid(axis='x', visible=False)
    save(fig, output_dir, 'main_seed_variation')


def plot_sampling(summary, output_dir):
    rows = [item for item in summary if item['suite'] == 'sampling']
    if not rows:
        return
    fig, axis = plt.subplots(figsize=(6.5, 4.2), constrained_layout=True)
    x = np.arange(len(rows))
    axis.bar(
        x,
        [item['top1_mean'] * 100 for item in rows],
        color=COLORS['sampling'],
        yerr=[item['top1_std'] * 100 for item in rows],
        capsize=3)
    for index, item in enumerate(rows):
        axis.text(
            index, item['top1_mean'] * 100 + 1.5,
            f"{item['top1_mean'] * 100:.1f}", ha='center', fontsize=8)
    axis.set_xticks(x, [item['label'] for item in rows])
    axis.set_ylabel('Top-1 / %')
    axis.set_ylim(0, 100)
    axis.grid(axis='x', visible=False)
    save(fig, output_dir, 'sampling_comparison')


def plot_budget(summary, output_dir):
    rows = [item for item in summary if item['suite'] == 'budget']
    if not rows:
        return
    fig, axis = plt.subplots(figsize=(6.8, 4.3), constrained_layout=True)
    x = np.arange(len(rows))
    axis.bar(
        x,
        [item['top1_mean'] * 100 for item in rows],
        color=COLORS['budget'],
        yerr=[item['top1_std'] * 100 for item in rows],
        capsize=3)
    for index, item in enumerate(rows):
        axis.text(
            index, item['top1_mean'] * 100 + 1.5,
            f"{item['top1_mean'] * 100:.1f}", ha='center', fontsize=8)
    axis.set_xticks(x, [item['label'] for item in rows])
    axis.set_ylabel('Top-1 / %')
    axis.set_ylim(0, 100)
    axis.grid(axis='x', visible=False)
    save(fig, output_dir, 'time_space_budget')


def write_sources(rows, summary, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / 'experiment_matrix_rows.csv').open(
            'w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                'suite', 'config', 'seed', 'top1', 'top5',
                'probe_type', 'feature_dir', 'metrics_path'])
        writer.writeheader()
        writer.writerows([
            {key: row[key] for key in writer.fieldnames}
            for row in rows
        ])
    (output_dir / 'experiment_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding='utf-8')


def main():
    args = parse_args()
    configure()
    rows = json.loads(args.matrix.read_text(encoding='utf-8'))
    summary = summarize(rows)
    write_sources(rows, summary, args.output_dir)
    plot_main(summary, args.output_dir)
    plot_seed_variation(rows, args.output_dir)
    plot_sampling(summary, args.output_dir)
    plot_budget(summary, args.output_dir)
    print(f'Figures: {args.output_dir}')


if __name__ == '__main__':
    main()
