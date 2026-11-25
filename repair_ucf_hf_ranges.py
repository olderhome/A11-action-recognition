import argparse
import concurrent.futures
import json
import struct
import time
import zlib
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_URL = (
    'https://hf-mirror.com/datasets/quchenyuan/UCF101-ZIP/'
    'resolve/main/UCF-101.zip')


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            'Repair damaged UCF101 ZIP members by downloading only their '
            'byte ranges from a full-archive mirror.'))
    parser.add_argument(
        '--archive',
        type=Path,
        default=PROJECT_ROOT / 'mmaction2-main/data/ucf101/UCF-101.zip')
    parser.add_argument(
        '--manifest',
        type=Path,
        default=(
            PROJECT_ROOT /
            'mmaction2-main/data/ucf101/kaggle_manifest.json'))
    parser.add_argument(
        '--video-root',
        type=Path,
        default=(
            PROJECT_ROOT /
            'mmaction2-main/data/ucf101/extracted/UCF-101'))
    parser.add_argument('--url', default=DEFAULT_URL)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--retries', type=int, default=30)
    parser.add_argument('--limit', type=int, default=0)
    return parser.parse_args()


def range_bytes(url, start, end, retries, label):
    expected = end - start + 1
    headers = {
        'Range': f'bytes={start}-{end}',
        'User-Agent': 'codex-a11-range-repair/1.0',
    }
    for attempt in range(1, retries + 1):
        try:
            with requests.get(
                    url,
                    headers=headers,
                    stream=True,
                    timeout=(30, 120)) as response:
                if response.status_code != 206:
                    raise RuntimeError(
                        f'Expected HTTP 206, got {response.status_code}')
                content_range = response.headers.get('Content-Range', '')
                if not content_range.startswith(f'bytes {start}-{end}/'):
                    raise RuntimeError(
                        f'Unexpected Content-Range: {content_range}')
                data = bytearray()
                for block in response.iter_content(1024 * 1024):
                    if block:
                        data.extend(block)
                if len(data) != expected:
                    raise RuntimeError(
                        f'Expected {expected} bytes, got {len(data)}')
                return bytes(data)
        except Exception as error:
            if attempt == retries:
                raise
            print(
                f'{label}: range retry {attempt}/{retries}: {error!r}',
                flush=True)
            time.sleep(min(2 * attempt, 15))


def read_local_member(url, info, retries):
    prefix_size = min(
        65536,
        30 + len(info.filename.encode('utf-8')) +
        len(info.extra) + info.compress_size)
    prefix = range_bytes(
        url,
        info.header_offset,
        info.header_offset + prefix_size - 1,
        retries,
        info.filename)
    if prefix[:4] != b'PK\x03\x04':
        raise RuntimeError(
            f'Invalid local ZIP header at {info.header_offset}')
    header = struct.unpack('<4s5H3I2H', prefix[:30])
    name_length = header[9]
    extra_length = header[10]
    data_start = info.header_offset + 30 + name_length + extra_length
    compressed = range_bytes(
        url,
        data_start,
        data_start + info.compress_size - 1,
        retries,
        info.filename)
    if info.compress_type == 0:
        content = compressed
    elif info.compress_type == 8:
        content = zlib.decompress(compressed, -15)
    else:
        raise RuntimeError(
            f'Unsupported compression type {info.compress_type}')
    if len(content) != info.file_size:
        raise RuntimeError(
            f'Uncompressed size mismatch: expected {info.file_size}, '
            f'got {len(content)}')
    if (zlib.crc32(content) & 0xFFFFFFFF) != info.CRC:
        raise RuntimeError('CRC32 mismatch')
    return content


def main():
    args = parse_args()
    import zipfile

    source_rows = json.loads(args.manifest.read_text(encoding='utf-8'))
    expected = {}
    for row in source_rows:
        name = row['name']
        if name.startswith('UCF101/UCF-101/') and name.endswith('.avi'):
            expected[name] = int(row['size'])
    missing = []
    for archive_name, size in expected.items():
        relative = archive_name[len('UCF101/UCF-101/'):]
        path = args.video_root / relative
        if not path.exists() or path.stat().st_size != size:
            missing.append((archive_name, relative, path))
    print(f'Need {len(missing)} damaged or missing videos', flush=True)
    if not missing:
        return
    if args.limit > 0:
        missing = missing[:args.limit]

    with zipfile.ZipFile(args.archive) as archive:
        members = {info.filename: info for info in archive.infolist()}
    absent = [
        name for name, _, _ in missing
        if name[len('UCF101/'):] not in members
    ]
    if absent:
        raise RuntimeError(
            f'{len(absent)} missing entries are absent from ZIP index: '
            f'{absent[:10]}')

    results = []

    def repair(item):
        archive_name, relative, destination = item
        content = read_local_member(
            args.url,
            members[archive_name[len('UCF101/'):]],
            args.retries)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + '.part')
        temporary.write_bytes(content)
        temporary.replace(destination)
        return {
            'path': relative,
            'bytes': len(content),
            'status': 'ok',
        }

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.workers) as pool:
        futures = {pool.submit(repair, item): item for item in missing}
        for index, future in enumerate(
                concurrent.futures.as_completed(futures), start=1):
            item = futures[future]
            try:
                result = future.result()
            except Exception as error:
                result = {
                    'path': item[1],
                    'status': 'failed',
                    'error_type': type(error).__name__,
                    'error': str(error),
                }
            results.append(result)
            if index % 10 == 0 or result['status'] == 'failed':
                print(
                    f"{index}/{len(missing)} {result['path']} "
                    f"{result['status']}",
                    flush=True)

    report = {
        'total': len(missing),
        'succeeded': sum(row['status'] == 'ok' for row in results),
        'failed': [
            row for row in results if row['status'] == 'failed'
        ],
        'results': results,
    }
    report_path = args.manifest.with_name('hf_range_repair_report.json')
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding='utf-8')
    print(f'Report: {report_path}', flush=True)
    if report['failed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
