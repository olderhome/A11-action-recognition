import argparse
import csv
import json
import statistics
import time
import urllib.request
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def request_json(url, payload=None, timeout=240):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(
        url, data=data, headers=headers, method='POST' if data else 'GET')
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def route_rows(case, repeat, response, route_key):
    route = response['routes'][route_key]
    top5 = route['top5']
    reference = case['reference'].strip().lower()
    known = reference not in {'', '无明确动作标签', '实时采集，参考标签未知'}
    labels = [item['label'].strip().lower() for item in top5]
    return {
        'case_id': case['id'],
        'case_title': case['title'],
        'reference': case['reference'],
        'repeat': repeat,
        'route_key': route_key,
        'route_name': route['name'],
        'model': route['short_name'],
        'top1': top5[0]['label'],
        'top1_score': top5[0]['score'],
        'top5_labels': '|'.join(labels),
        'top1_correct': (
            int(labels[0] == reference) if known else None),
        'top5_correct': (
            int(reference in labels) if known else None),
        'elapsed_seconds': route['elapsed_seconds'],
        'throughput_videos_per_second': 1 / route['elapsed_seconds'],
        'parameters_million': route['parameters'] / 1e6,
        'parameter_mb': route['parameter_mb'],
        'gpu_resident_mb': response['summary']['gpu_resident_mb'],
        'gpu_peak_mb': response['summary']['gpu_peak_mb'],
    }


def aggregate(rows):
    groups = {}
    for row in rows:
        key = (row['case_id'], row['route_key'])
        groups.setdefault(key, []).append(row)

    summary = []
    for (_, _), group in groups.items():
        group = sorted(group, key=lambda item: item['repeat'])
        latencies = [item['elapsed_seconds'] for item in group]
        scores = [item['top1_score'] for item in group]
        top1_labels = {item['top1'] for item in group}
        correctness = [
            item['top1_correct'] for item in group
            if item['top1_correct'] is not None]
        summary.append({
            'case_id': group[0]['case_id'],
            'case_title': group[0]['case_title'],
            'reference': group[0]['reference'],
            'route_key': group[0]['route_key'],
            'route_name': group[0]['route_name'],
            'top1': group[0]['top1'],
            'top1_stable': len(top1_labels) == 1,
            'top1_score_mean': statistics.mean(scores),
            'top1_score_std': statistics.pstdev(scores),
            'latency_median_seconds': statistics.median(latencies),
            'latency_min_seconds': min(latencies),
            'latency_max_seconds': max(latencies),
            'throughput_median_videos_per_second': (
                1 / statistics.median(latencies)),
            'top1_accuracy': (
                statistics.mean(correctness) if correctness else None),
            'top5_correct': (
                all(item['top5_correct'] for item in group
                    if item['top5_correct'] is not None)
                if correctness else None),
            'parameters_million': group[0]['parameters_million'],
            'parameter_mb': group[0]['parameter_mb'],
            'gpu_resident_mb': group[0]['gpu_resident_mb'],
            'gpu_peak_mb': max(item['gpu_peak_mb'] for item in group),
        })
    return summary


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8-sig') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_report(path, rows, summary, repeats):
    known = [row for row in summary if row['top1_accuracy'] is not None]
    route_names = {
        'tsn_2d': 'TSN ResNet-50',
        'r2plus1d_3d': 'R(2+1)D ResNet-34',
    }
    lines = [
        '# A11 运行验证批量实验',
        '',
        f'- 运行时间：{datetime.now().isoformat(timespec="seconds")}',
        f'- 重复次数：{repeats}',
        f'- 测试视频数：{len({row["case_id"] for row in rows})}',
        '- 模型：Kinetics-400 预训练演示权重',
        '',
        '## 汇总',
        '',
        '| 用例 | 路线 | Top-1 | 置信度 | 耗时中位数 | 吞吐 | Top-5 校验 | 两模型 GPU 峰值 | Top-1 稳定 |',
        '|---|---|---|---:|---:|---:|---|---:|---|',
    ]
    for row in summary:
        top5_check = (
            '通过' if row['top5_correct'] else '未知'
            if row['top5_correct'] is None else '失败')
        lines.append(
            f"| {row['case_title']} | {route_names[row['route_key']]} | "
            f"{row['top1']} | {row['top1_score_mean'] * 100:.2f}% | "
            f"{row['latency_median_seconds']:.3f} s | "
            f"{row['throughput_median_videos_per_second']:.2f} video/s | "
            f"{top5_check} | {row['gpu_peak_mb']:.0f} MiB | "
            f"{'是' if row['top1_stable'] else '否'} |")
    lines.extend([
        '',
        '## 范围说明',
        '',
        '本次实验使用现有短视频和 Kinetics-400 演示权重，验证推理链路、两条路线差异、'
        '结果稳定性和吞吐。视频级重复运行不等同于训练随机种子实验；由于尚未准备 UCF101 '
        '训练数据与 101 类模型，本结果不能用于验收“相对 3D 基线提升 4 个百分点”或'
        '“训练峰值显存不超过 2 GB”。',
    ])
    if known:
        lines.extend([
            '',
            '已知参考标签的用例中：',
            '',
        ])
        for route_key in ('tsn_2d', 'r2plus1d_3d'):
            route_rows_known = [
                item for item in known if item['route_key'] == route_key]
            accuracy = statistics.mean(
                item['top1_accuracy'] for item in route_rows_known)
            lines.append(
                f'- {route_names[route_key]}：Top-1 准确率 '
                f'{accuracy * 100:.1f}%。')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Run all dashboard testcases repeatedly and export results.')
    parser.add_argument('--base-url', default='http://127.0.0.1:7860')
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument(
        '--output-dir', type=Path,
        default=PROJECT_ROOT / 'outputs' / 'experiments')
    return parser.parse_args()


def main():
    args = parse_args()
    health = request_json(f'{args.base_url}/api/health')
    if not health.get('ok'):
        raise RuntimeError('Comparison dashboard is not available.')
    cases = request_json(f'{args.base_url}/api/testcases')['cases']
    if not cases:
        raise RuntimeError('No test cases are available.')

    run_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = args.output_dir / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    started = time.perf_counter()

    for repeat in range(1, args.repeats + 1):
        for case in cases:
            print(f'[{repeat}/{args.repeats}] {case["title"]}')
            response = request_json(
                f'{args.base_url}/api/run', {'case_id': case['id']})
            for route_key in ('tsn_2d', 'r2plus1d_3d'):
                rows.append(route_rows(case, repeat, response, route_key))

    summary = aggregate(rows)
    write_csv(output_dir / 'runs.csv', rows)
    write_csv(output_dir / 'summary.csv', summary)
    (output_dir / 'summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    (output_dir / 'environment.json').write_text(
        json.dumps({
            'health': health,
            'repeats': args.repeats,
            'testcases': cases,
            'duration_seconds': time.perf_counter() - started,
        }, ensure_ascii=False, indent=2), encoding='utf-8')
    write_report(output_dir / 'REPORT.md', rows, summary, args.repeats)
    print(f'Experiment output: {output_dir}')


if __name__ == '__main__':
    main()
