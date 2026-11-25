import argparse
import concurrent.futures
import json
import shutil
import sys
from pathlib import Path


_SCRIPT_ARGV = sys.argv[:]
sys.argv = ['kaggle', 'datasets', 'download']
from kaggle.api.kaggle_api_extended import KaggleApi
sys.argv = _SCRIPT_ARGV


PROJECT_ROOT = Path(__file__).resolve().parent


def parse_args():
    parser = argparse.ArgumentParser(
        description='Repair missing UCF101 files with Kaggle API.')
    parser.add_argument(
        '--missing',
        type=Path,
        default=(
            PROJECT_ROOT /
            'mmaction2-main/data/ucf101/missing_files.json'))
    parser.add_argument(
        '--extract-root',
        type=Path,
        default=(
            PROJECT_ROOT /
            'mmaction2-main/data/ucf101/extracted'))
    parser.add_argument(
        '--staging-root',
        type=Path,
        default=(
            PROJECT_ROOT /
            'mmaction2-main/data/ucf101/kaggle_repair'))
    parser.add_argument('--workers', type=int, default=8)
    return parser.parse_args()


def main():
    args = parse_args()
    api = KaggleApi()
    script_argv = sys.argv[:]
    sys.argv = ['kaggle', 'datasets', 'download']
    api.authenticate()
    sys.argv = script_argv
    if not api._authenticated:
        raise RuntimeError('Anonymous Kaggle API authentication failed.')
    missing = json.loads(args.missing.read_text(encoding='utf-8'))
    print(f'Repairing {len(missing)} files with {args.workers} workers')
    results = []

    def repair(item):
        name = item['name']
        expected = int(item['size'])
        relative = name[len('UCF101/'):]
        destination = args.extract_root / relative
        staging = args.staging_root / name
        if destination.exists() and destination.stat().st_size == expected:
            return {'name': name, 'status': 'ok', 'attempts': 0}
        if staging.exists() and staging.stat().st_size == expected:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(staging, destination)
            return {'name': name, 'status': 'ok', 'attempts': 0}
        if staging.exists():
            staging.unlink()
        for attempt in range(1, 6):
            try:
                api.dataset_download_file(
                    'pevogam/ucf101',
                    name,
                    path=str(args.staging_root),
                    force=True,
                    quiet=True,
                    unzip=True,
                )
            except Exception as error:
                print(f'{name} attempt {attempt}: {error!r}', flush=True)
            if staging.exists() and staging.stat().st_size == expected:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(staging, destination)
                return {
                    'name': name,
                    'status': 'ok',
                    'attempts': attempt,
                }
        return {'name': name, 'status': 'failed', 'attempts': 5}

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.workers) as pool:
        futures = [pool.submit(repair, item) for item in missing]
        for index, future in enumerate(
                concurrent.futures.as_completed(futures), start=1):
            result = future.result()
            results.append(result)
            if index % 20 == 0 or result['status'] == 'failed':
                print(f'{index}/{len(missing)} {result}', flush=True)

    failed = [item for item in results if item['status'] == 'failed']
    report = args.missing.with_name('kaggle_api_repair_report.json')
    report.write_text(
        json.dumps({
            'total': len(missing),
            'succeeded': len(results) - len(failed),
            'failed': failed,
            'results': results,
        }, ensure_ascii=False, indent=2),
        encoding='utf-8')
    if failed:
        raise RuntimeError(f'{len(failed)} files failed')
    print(f'Repair complete: {report}')


if __name__ == '__main__':
    main()
