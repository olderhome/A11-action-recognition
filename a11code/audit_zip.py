import argparse
import collections
import zipfile
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description='Read every ZIP member and identify damaged source chunks.')
    parser.add_argument('archive', type=Path)
    parser.add_argument('--chunk-size', type=int, default=434835854)
    parser.add_argument('--max-errors', type=int, default=30)
    return parser.parse_args()


def main():
    args = parse_args()
    errors = []
    checked = 0
    with zipfile.ZipFile(args.archive) as archive:
        for info in archive.infolist():
            checked += 1
            try:
                with archive.open(info) as handle:
                    while handle.read(1024 * 1024):
                        pass
            except Exception as error:
                errors.append({
                    'file': info.filename,
                    'header_offset': info.header_offset,
                    'suspected_chunk': info.header_offset // args.chunk_size,
                    'error_type': type(error).__name__,
                    'error': str(error),
                })
                print(
                    len(errors), info.filename, info.header_offset,
                    info.header_offset // args.chunk_size,
                    type(error).__name__, str(error))
                if len(errors) >= args.max_errors:
                    break
    print(
        'checked', checked, 'errors', len(errors), 'suspected_chunks',
        dict(collections.Counter(
            item['suspected_chunk'] for item in errors)))


if __name__ == '__main__':
    main()
