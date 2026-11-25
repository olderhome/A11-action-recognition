import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

from scipy import stats


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args():
    parser = argparse.ArgumentParser(
        description='Aggregate A11 seed results and paired comparisons.')
    parser.add_argument('--matrix', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = json.loads(args.matrix.read_text(encoding='utf-8'))
    grouped = defaultdict(dict)
    for row in rows:
        grouped[
            (row['suite'], row['config'], row['probe_type'])
        ][row['seed']] = row

    aggregate = []
    for (suite, config, probe_type), seed_rows in grouped.items():
        values = list(seed_rows.values())
        top1 = [item['top1'] for item in values]
        top5 = [item['top5'] for item in values]
        aggregate.append({
            'suite': suite,
            'config': config,
            'probe_type': probe_type,
            'seeds': sorted(seed_rows),
            'seed_count': len(seed_rows),
            'top1_mean': statistics.mean(top1),
            'top1_std': (
                statistics.stdev(top1) if len(top1) > 1 else 0.0),
            'top5_mean': statistics.mean(top5),
            'top5_std': (
                statistics.stdev(top5) if len(top5) > 1 else 0.0),
            'max_peak_mib': max(
                item['max_memory_reserved_mib'] for item in values),
            'feature_peak_mib': max(
                item['feature_metrics']['test']['max_memory_reserved_mib']
                for item in values),
        })

    comparisons = []
    baseline_key = ('main', 'r3d18_uniform', 'linear')
    if baseline_key in grouped:
        baseline = grouped[baseline_key]
        for (suite, config, probe_type), seed_rows in grouped.items():
            if suite != 'main' or config == baseline_key[1]:
                continue
            common = sorted(set(seed_rows) & set(baseline))
            if not common:
                continue
            differences = [
                seed_rows[seed]['top1'] - baseline[seed]['top1']
                for seed in common
            ]
            if len(differences) > 1:
                test = stats.ttest_rel(
                    [seed_rows[seed]['top1'] for seed in common],
                    [baseline[seed]['top1'] for seed in common])
                p_value = float(test.pvalue)
            else:
                p_value = None
            comparisons.append({
                'candidate': config,
                'candidate_probe': probe_type,
                'baseline': baseline_key[1],
                'seeds': common,
                'delta_mean': statistics.mean(differences),
                'delta_std': (
                    statistics.stdev(differences)
                    if len(differences) > 1 else 0.0),
                'meets_4pp': statistics.mean(differences) >= 0.04,
                'paired_p_value': p_value,
            })

    if aggregate:
        with (args.output_dir / 'aggregate.csv').open(
                'w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(
                handle, fieldnames=list(aggregate[0].keys()))
            writer.writeheader()
            writer.writerows(aggregate)
    if comparisons:
        with (args.output_dir / 'comparisons.csv').open(
                'w', newline='', encoding='utf-8') as handle:
            writer = csv.DictWriter(
                handle, fieldnames=list(comparisons[0].keys()))
            writer.writeheader()
            writer.writerows(comparisons)
    result = {
        'aggregate': aggregate,
        'comparisons': comparisons,
    }
    (args.output_dir / 'summary.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
