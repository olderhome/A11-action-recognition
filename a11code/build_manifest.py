import argparse
import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    parser = argparse.ArgumentParser(
        description='Build and validate UCF101 split manifests.')
    parser.add_argument(
        '--data-root',
        type=Path,
        default=PROJECT_ROOT / 'mmaction2-main/data/ucf101')
    parser.add_argument(
        '--output-root',
        type=Path,
        default=PROJECT_ROOT / 'results/data')
    parser.add_argument('--split', type=int, default=1)
    return parser.parse_args()


def group_key(relative_path):
    class_name = Path(relative_path).parts[0]
    stem = Path(relative_path).stem
    parts = stem.split('_')
    if len(parts) < 3:
        raise ValueError(f'Cannot parse group from {relative_path}')
    return f'{class_name}/{parts[2]}'


def main():
    args = parse_args()
    annotation_root = (
        args.data_root / 'annotations/ucfTrainTestlist')
    video_root = args.data_root / 'videos'
    if not video_root.exists():
        raise FileNotFoundError(
            f'UCF101 videos are not extracted at {video_root}')

    classes = {}
    for line in (annotation_root / 'classInd.txt').read_text(
            encoding='utf-8').splitlines():
        label, name = line.split(maxsplit=1)
        classes[name.strip()] = int(label) - 1
    if len(classes) != 101:
        raise RuntimeError(f'Expected 101 classes, got {len(classes)}')

    def read_split(kind):
        path = annotation_root / f'{kind}list{args.split:02d}.txt'
        rows = []
        for line in path.read_text(encoding='utf-8').splitlines():
            parts = line.split()
            relative = parts[0]
            class_name = Path(relative).parts[0]
            label = classes[class_name]
            absolute = video_root / relative
            if not absolute.exists():
                raise FileNotFoundError(absolute)
            rows.append({
                'path': relative,
                'label': label,
                'class_name': class_name,
                'group': group_key(relative),
            })
        return rows

    train_rows = read_split('train')
    test_rows = read_split('test')
    class_groups = {}
    for row in train_rows:
        class_groups.setdefault(row['class_name'], set()).add(row['group'])
    validation_groups = set()
    for groups in class_groups.values():
        validation_groups.update(sorted(groups)[-2:])
    val_rows = [
        row for row in train_rows if row['group'] in validation_groups]
    train_fit_rows = [
        row for row in train_rows if row['group'] not in validation_groups]
    train_groups = {row['group'] for row in train_fit_rows}
    val_group_set = {row['group'] for row in val_rows}
    test_groups = {row['group'] for row in test_rows}
    overlaps = [
        ('train/test', train_groups & test_groups),
        ('train/val', train_groups & val_group_set),
        ('val/test', val_group_set & test_groups),
    ]
    for name, overlap in overlaps:
        if overlap:
            raise RuntimeError(
                f'Group leakage detected in {name}: {sorted(overlap)[:10]}')
    if {
            row['label']
            for row in train_fit_rows + val_rows + test_rows
    } != set(range(101)):
        raise RuntimeError('Some classes are missing from split.')

    args.output_root.mkdir(parents=True, exist_ok=True)
    for name, rows in [
            ('train', train_rows),
            ('train_fit', train_fit_rows),
            ('val', val_rows),
            ('test', test_rows)]:
        output = args.output_root / f'ucf101_split{args.split}_{name}.csv'
        with output.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=['path', 'label', 'class_name', 'group'])
            writer.writeheader()
            writer.writerows(rows)

    summary = {
        'split': args.split,
        'classes': len(classes),
        'train_videos': len(train_rows),
        'train_fit_videos': len(train_fit_rows),
        'validation_videos': len(val_rows),
        'test_videos': len(test_rows),
        'train_class_groups': len(train_groups),
        'validation_class_groups': len(val_group_set),
        'test_class_groups': len(test_groups),
        'group_overlap': sum(len(value) for _, value in overlaps),
        'video_root': str(video_root),
    }
    (args.output_root / f'ucf101_split{args.split}_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
