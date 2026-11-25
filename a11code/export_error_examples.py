import argparse
import csv
import json
from pathlib import Path

import cv2
import numpy as np

try:
    import decord
except ImportError as error:
    raise RuntimeError('decord is required') from error


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    parser = argparse.ArgumentParser(
        description='Export representative misclassified UCF101 videos.')
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument(
        '--video-root',
        type=Path,
        default=PROJECT_ROOT / 'mmaction2-main/data/ucf101/videos')
    parser.add_argument(
        '--class-file',
        type=Path,
        default=(PROJECT_ROOT /
                 'mmaction2-main/data/ucf101/annotations/'
                 'ucfTrainTestlist/classInd.txt'))
    parser.add_argument('--limit', type=int, default=12)
    return parser.parse_args()


def read_classes(path):
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        index, name = line.split(maxsplit=1)
        rows.append((int(index) - 1, name.strip()))
    return [name for _, name in sorted(rows)]


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    classes = read_classes(args.class_file)
    with args.predictions.open(newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    errors = [
        row for row in rows
        if int(row['label']) != int(row['prediction'])
    ]
    errors.sort(
        key=lambda row: (-float(row['score']), row['path']))

    selected = []
    seen_true = set()
    for row in errors:
        label = int(row['label'])
        if label in seen_true:
            continue
        selected.append(row)
        seen_true.add(label)
        if len(selected) >= args.limit:
            break
    if len(selected) < args.limit:
        for row in errors:
            if row not in selected:
                selected.append(row)
            if len(selected) >= args.limit:
                break

    metadata = []
    for index, row in enumerate(selected, start=1):
        video_path = args.video_root / row['path']
        reader = decord.VideoReader(str(video_path), num_threads=2)
        frame_index = max(0, len(reader) // 2)
        frame = reader.get_batch([frame_index]).asnumpy()[0]
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        frame = cv2.resize(
            frame, (480, 360), interpolation=cv2.INTER_AREA)
        true_label = int(row['label'])
        prediction = int(row['prediction'])
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (480, 72), (20, 20, 20), -1)
        frame = cv2.addWeighted(overlay, 0.8, frame, 0.2, 0)
        cv2.putText(
            frame,
            f"true: {classes[true_label]}",
            (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
            (240, 240, 240), 1, cv2.LINE_AA)
        cv2.putText(
            frame,
            f"pred: {classes[prediction]}  {float(row['score']):.3f}",
            (12, 54), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
            (150, 180, 245), 1, cv2.LINE_AA)
        filename = f'error_{index:02d}.jpg'
        ok, encoded = cv2.imencode(
            '.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not ok:
            raise RuntimeError(f'Unable to encode {filename}')
        (args.output_dir / filename).write_bytes(encoded.tobytes())
        metadata.append({
            'file': filename,
            'path': row['path'],
            'true_index': true_label,
            'true_class': classes[true_label],
            'predicted_index': prediction,
            'predicted_class': classes[prediction],
            'confidence': float(row['score']),
        })
    (args.output_dir / 'error_examples.json').write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding='utf-8')
    print(f'Exported {len(metadata)} examples to {args.output_dir}')


if __name__ == '__main__':
    main()
