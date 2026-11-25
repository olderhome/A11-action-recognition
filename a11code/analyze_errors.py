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


def configure_plotting():
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


def parse_args():
    parser = argparse.ArgumentParser(
        description='Analyze UCF101 predictions and generate error figures.')
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument(
        '--class-file',
        type=Path,
        default=(PROJECT_ROOT /
                 'mmaction2-main/data/ucf101/annotations/'
                 'ucfTrainTestlist/classInd.txt'))
    parser.add_argument('--output-dir', type=Path, required=True)
    return parser.parse_args()


def read_classes(path):
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        index, name = line.split(maxsplit=1)
        rows.append((int(index) - 1, name.strip()))
    rows.sort()
    if [index for index, _ in rows] != list(range(101)):
        raise RuntimeError('Class index file is not exactly 0-100 after mapping.')
    return [name for _, name in rows]


def read_predictions(path):
    with path.open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    labels = np.asarray([int(row['label']) for row in rows])
    predictions = np.asarray([int(row['prediction']) for row in rows])
    return rows, labels, predictions


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    configure_plotting()
    class_names = read_classes(args.class_file)
    rows, labels, predictions = read_predictions(args.predictions)
    if labels.shape != predictions.shape or labels.size == 0:
        raise RuntimeError('Prediction file has invalid labels.')

    confusion = np.zeros((101, 101), dtype=np.int64)
    for label, prediction in zip(labels, predictions):
        confusion[label, prediction] += 1
    support = confusion.sum(axis=1)
    correct = np.diag(confusion)
    recall = np.divide(
        correct, support, out=np.zeros(101, dtype=float), where=support > 0)
    predicted_total = confusion.sum(axis=0)
    precision = np.divide(
        correct, predicted_total, out=np.zeros(101, dtype=float),
        where=predicted_total > 0)

    per_class = []
    for index, name in enumerate(class_names):
        per_class.append({
            'class_index': index,
            'class_name': name,
            'support': int(support[index]),
            'correct': int(correct[index]),
            'recall': float(recall[index]),
            'precision': float(precision[index]),
        })
    per_class.sort(key=lambda item: (item['recall'], -item['support']))
    with (args.output_dir / 'per_class_metrics.csv').open(
            'w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(per_class[0]))
        writer.writeheader()
        writer.writerows(per_class)

    conflicts = []
    for true_index in range(101):
        for predicted_index in range(101):
            if true_index == predicted_index:
                continue
            count = int(confusion[true_index, predicted_index])
            if count > 0:
                conflicts.append({
                    'true_index': true_index,
                    'true_class': class_names[true_index],
                    'predicted_index': predicted_index,
                    'predicted_class': class_names[predicted_index],
                    'count': count,
                })
    conflicts.sort(key=lambda item: item['count'], reverse=True)
    with (args.output_dir / 'top_confusions.csv').open(
            'w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(conflicts[0]))
        writer.writeheader()
        writer.writerows(conflicts[:200])

    np.save(args.output_dir / 'confusion_matrix.npy', confusion)
    normalized = np.divide(
        confusion, support[:, None],
        out=np.zeros_like(confusion, dtype=float),
        where=support[:, None] > 0)

    fig, axis = plt.subplots(figsize=(10, 8.5), constrained_layout=True)
    image = axis.imshow(
        normalized, cmap='magma', vmin=0, vmax=max(0.25, normalized.max()),
        interpolation='nearest')
    axis.set_xlabel('预测类别')
    axis.set_ylabel('真实类别')
    axis.set_xticks([])
    axis.set_yticks([])
    fig.colorbar(image, ax=axis, shrink=0.78, label='按真实类归一化比例')
    fig.savefig(args.output_dir / 'confusion_matrix.png')
    fig.savefig(args.output_dir / 'confusion_matrix.pdf')
    plt.close(fig)

    worst = per_class[:15][::-1]
    fig, axis = plt.subplots(figsize=(8.5, 5.5), constrained_layout=True)
    axis.barh(
        [item['class_name'] for item in worst],
        [item['recall'] * 100 for item in worst],
        color='#B64C4C')
    axis.set_xlabel('类别召回率 / %')
    axis.set_xlim(0, 100)
    axis.grid(axis='y', visible=False)
    fig.savefig(args.output_dir / 'worst_class_recall.png')
    fig.savefig(args.output_dir / 'worst_class_recall.pdf')
    plt.close(fig)

    summary = {
        'samples': int(labels.size),
        'top1': float((labels == predictions).mean()),
        'mean_recall': float(recall.mean()),
        'worst_classes': per_class[:15],
        'top_confusions': conflicts[:20],
    }
    (args.output_dir / 'error_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
