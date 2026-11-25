import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    parser = argparse.ArgumentParser(
        description='Plot UCF101 split and class distribution.')
    parser.add_argument(
        '--manifest-root',
        type=Path,
        default=PROJECT_ROOT / 'results/data')
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=PROJECT_ROOT / 'figures')
    return parser.parse_args()


def read_manifest(path):
    with path.open(newline='', encoding='utf-8') as handle:
        return list(csv.DictReader(handle))


def configure():
    font_path = Path('C:/Windows/Fonts/msyh.ttc')
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        plt.rcParams['font.family'] = 'Microsoft YaHei'
    plt.rcParams.update({
        'axes.unicode_minus': False,
        'font.size': 9,
        'savefig.dpi': 320,
        'savefig.bbox': 'tight',
        'axes.spines.top': False,
        'axes.spines.right': False,
    })


def main():
    args = parse_args()
    configure()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    train = read_manifest(
        args.manifest_root / 'ucf101_split1_train.csv')
    test = read_manifest(
        args.manifest_root / 'ucf101_split1_test.csv')
    names = sorted({row['class_name'] for row in train + test})
    name_to_index = {name: index for index, name in enumerate(names)}
    train_counts = Counter(row['class_name'] for row in train)
    test_counts = Counter(row['class_name'] for row in test)
    train_values = np.asarray(
        [train_counts[name] for name in names], dtype=int)
    test_values = np.asarray(
        [test_counts[name] for name in names], dtype=int)

    order = np.argsort(train_values + test_values)
    fig, axis = plt.subplots(figsize=(15, 5.4), constrained_layout=True)
    x = np.arange(len(names))
    axis.bar(
        x, train_values[order], color='#176F6B', label='训练集')
    axis.bar(
        x, test_values[order], bottom=train_values[order],
        color='#C46A18', label='测试集')
    step = max(1, len(names) // 30)
    axis.set_xticks(
        x[::step],
        [names[index] for index in order[::step]],
        rotation=60,
        ha='right')
    axis.set_ylabel('视频数')
    axis.legend(frameon=False)
    axis.grid(axis='x', visible=False)
    fig.savefig(args.output_dir / 'dataset_class_distribution.pdf')
    fig.savefig(args.output_dir / 'dataset_class_distribution.png')
    plt.close(fig)

    groups = {}
    for split, rows in [('train', train), ('test', test)]:
        groups[split] = sorted({row['group'] for row in rows})
    summary = {
        'classes': len(names),
        'train_videos': len(train),
        'test_videos': len(test),
        'train_class_groups': len(groups['train']),
        'test_class_groups': len(groups['test']),
        'group_overlap': len(
            set(groups['train']) & set(groups['test'])),
        'train_count_min': int(train_values.min()),
        'train_count_max': int(train_values.max()),
        'test_count_min': int(test_values.min()),
        'test_count_max': int(test_values.max()),
    }
    (args.output_dir / 'dataset_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding='utf-8')
    with (args.output_dir / 'dataset_class_counts.csv').open(
            'w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle)
        writer.writerow(['class_name', 'train', 'test'])
        for name, train_count, test_count in zip(
                names, train_values, test_values):
            writer.writerow([name, train_count, test_count])
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
