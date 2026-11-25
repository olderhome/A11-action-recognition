import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use('Agg')

import matplotlib.font_manager as font_manager
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUTE_LABELS = {
    'tsn_2d': 'TSN-2D',
    'r2plus1d_3d': 'R(2+1)D-3D',
}
ROUTE_COLORS = {
    'tsn_2d': '#177D78',
    'r2plus1d_3d': '#C66A18',
}
CASE_SHORT = {
    '掰手腕示例': '掰手腕',
    '摄像头人物近景': '人物近景',
    '新摄像头片段 1': '摄像片段 1',
    '新摄像头片段 2': '摄像片段 2',
    '新摄像头片段 3': '摄像片段 3',
}


def configure_fonts():
    font_path = Path('C:/Windows/Fonts/msyh.ttc')
    if font_path.exists():
        font_manager.fontManager.addfont(str(font_path))
        plt.rcParams['font.family'] = 'Microsoft YaHei'
    plt.rcParams.update({
        'axes.unicode_minus': False,
        'font.size': 10,
        'axes.titlesize': 11,
        'axes.labelsize': 10,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.dpi': 120,
        'savefig.dpi': 320,
        'savefig.bbox': 'tight',
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': True,
        'grid.color': '#D7D9DB',
        'grid.linewidth': 0.6,
        'grid.alpha': 0.7,
    })


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle))


def numeric(row, key):
    row[key] = float(row[key]) if row[key] not in ('', 'None') else None


def save_figure(fig, output_dir, stem):
    fig.savefig(output_dir / f'{stem}.png')
    fig.savefig(output_dir / f'{stem}.pdf')
    plt.close(fig)


def ordered_cases(summary):
    seen = []
    for row in summary:
        if row['case_title'] not in seen:
            seen.append(row['case_title'])
    return seen


def route_lookup(summary):
    return {
        (row['case_title'], row['route_key']): row
        for row in summary
    }


def figure_latency_throughput(summary, output_dir):
    cases = ordered_cases(summary)
    lookup = route_lookup(summary)
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 5.2), constrained_layout=True)
    y = np.arange(len(cases))
    height = 0.34

    for offset, route_key in [(-height / 2, 'tsn_2d'),
                              (height / 2, 'r2plus1d_3d')]:
        latency = [
            lookup[(case, route_key)]['latency_median_seconds'] * 1000
            for case in cases
        ]
        throughput = [
            lookup[(case, route_key)]['throughput_median_videos_per_second']
            for case in cases
        ]
        axes[0].barh(
            y + offset, latency, height, color=ROUTE_COLORS[route_key],
            label=ROUTE_LABELS[route_key])
        axes[1].barh(
            y + offset, throughput, height, color=ROUTE_COLORS[route_key],
            label=ROUTE_LABELS[route_key])
        for index, value in enumerate(latency):
            axes[0].text(
                value + 5, y[index] + offset, f'{value:.0f}',
                va='center', fontsize=8)
        for index, value in enumerate(throughput):
            axes[1].text(
                value + 0.08, y[index] + offset, f'{value:.2f}',
                va='center', fontsize=8)

    short_cases = [CASE_SHORT.get(case, case) for case in cases]
    for axis in axes:
        axis.set_yticks(y, short_cases)
        axis.invert_yaxis()
        axis.grid(axis='y', visible=False)
    axes[0].set_title('端到端单视频推理耗时')
    axes[0].set_xlabel('耗时 / ms')
    axes[0].set_xlim(0, max(
        row['latency_median_seconds'] * 1000 for row in summary) * 1.18)
    axes[1].set_title('端到端单视频吞吐')
    axes[1].set_xlabel('吞吐 / video/s')
    axes[1].set_xlim(0, max(
        row['throughput_median_videos_per_second']
        for row in summary) * 1.18)
    axes[0].legend(frameon=False, loc='lower right')
    save_figure(fig, output_dir, 'fig01_latency_throughput')


def short_label(value):
    aliases = {
        'arm wrestling': 'arm wrestling',
        'rock scissors paper': 'rock scissors',
        'massaging feet': 'massaging feet',
        'stretching leg': 'stretching leg',
        'bench pressing': 'bench press',
        'eating chips': 'eating chips',
        'cracking neck': 'cracking neck',
        'shaking head': 'shaking head',
        'eating burger': 'eating burger',
        'smoking': 'smoking',
        'beatboxing': 'beatboxing',
    }
    return aliases.get(value, value)


def figure_top1_confidence(summary, output_dir):
    cases = ordered_cases(summary)
    lookup = route_lookup(summary)
    fig, axis = plt.subplots(figsize=(10.5, 5.2), constrained_layout=True)
    x = np.arange(len(cases))
    width = 0.36

    for offset, route_key in [(-width / 2, 'tsn_2d'),
                              (width / 2, 'r2plus1d_3d')]:
        values = [
            lookup[(case, route_key)]['top1_score_mean'] * 100
            for case in cases
        ]
        bars = axis.bar(
            x + offset, values, width, color=ROUTE_COLORS[route_key],
            label=ROUTE_LABELS[route_key])
        for bar, case in zip(bars, cases):
            label = short_label(
                lookup[(case, route_key)]['top1'])
            axis.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 2,
                label,
                ha='center',
                va='bottom',
                rotation=32 if len(cases) > 3 else 0,
                fontsize=8)

    axis.set_xticks(
        x, [CASE_SHORT.get(case, case) for case in cases])
    axis.set_ylabel('Top-1 置信度 / %')
    axis.set_ylim(0, 125)
    axis.set_title('两条路线的 Top-1 标签与置信度')
    axis.legend(frameon=False, loc='upper right')
    axis.grid(axis='x', visible=False)
    save_figure(fig, output_dir, 'fig02_top1_confidence')


def figure_confidence_delta(summary, output_dir):
    cases = ordered_cases(summary)
    lookup = route_lookup(summary)
    delta = []
    agreement = []
    for case in cases:
        tsn = lookup[(case, 'tsn_2d')]
        r3d = lookup[(case, 'r2plus1d_3d')]
        delta.append(
            (tsn['top1_score_mean'] - r3d['top1_score_mean']) * 100)
        agreement.append(tsn['top1'].lower() == r3d['top1'].lower())

    fig, axis = plt.subplots(figsize=(9.6, 4.4), constrained_layout=True)
    y = np.arange(len(cases))
    colors = ['#157F78' if value >= 0 else '#B64342' for value in delta]
    axis.barh(y, delta, color=colors, height=0.55)
    axis.axvline(0, color='#4B5156', linewidth=1)
    for index, value in enumerate(delta):
        axis.text(
            value + (1.5 if value >= 0 else -1.5),
            y[index],
            f'{value:+.1f} pp',
            va='center',
            ha='left' if value >= 0 else 'right',
            fontsize=9)
    axis.set_yticks(
        y,
        [
            f"{CASE_SHORT.get(case, case)}  "
            f"({'一致' if agree else '冲突'})"
            for case, agree in zip(cases, agreement)
        ])
    axis.invert_yaxis()
    axis.set_xlabel('Top-1 置信度差：TSN-2D 减 R(2+1)D-3D / 百分点')
    axis.set_title('路线置信度差与 Top-1 一致性')
    span = max(abs(min(delta)), abs(max(delta)), 1)
    axis.set_xlim(-span * 1.35, span * 1.35)
    axis.grid(axis='y', visible=False)
    save_figure(fig, output_dir, 'fig03_confidence_delta')


def figure_repeat_stability(summary, output_dir):
    cases = ordered_cases(summary)
    lookup = route_lookup(summary)
    fig, axis = plt.subplots(figsize=(10.5, 5.2), constrained_layout=True)
    x = np.arange(len(cases))
    width = 0.36

    for offset, route_key in [(-width / 2, 'tsn_2d'),
                              (width / 2, 'r2plus1d_3d')]:
        rows = [lookup[(case, route_key)] for case in cases]
        median = np.array([
            row['latency_median_seconds'] * 1000 for row in rows])
        lower = median - np.array([
            row['latency_min_seconds'] * 1000 for row in rows])
        upper = np.array([
            row['latency_max_seconds'] * 1000 for row in rows]) - median
        axis.bar(
            x + offset, median, width, color=ROUTE_COLORS[route_key],
            label=ROUTE_LABELS[route_key], yerr=np.vstack([lower, upper]),
            capsize=3, error_kw={'elinewidth': 1, 'ecolor': '#3F4549'})

    axis.set_xticks(
        x, [CASE_SHORT.get(case, case) for case in cases])
    axis.set_ylabel('耗时中位数及最小–最大范围 / ms')
    axis.set_title('三次重复运行的时延波动')
    axis.legend(frameon=False)
    axis.grid(axis='x', visible=False)
    save_figure(fig, output_dir, 'fig04_repeat_latency')


def figure_model_complexity(summary, output_dir):
    first = {}
    for row in summary:
        first.setdefault(row['route_key'], row)
    routes = ['tsn_2d', 'r2plus1d_3d']
    parameter_m = [first[route]['parameters_million'] for route in routes]
    parameter_mb = [first[route]['parameter_mb'] for route in routes]
    labels = [ROUTE_LABELS[route] for route in routes]
    colors = [ROUTE_COLORS[route] for route in routes]

    fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.4), constrained_layout=True)
    axes[0].bar(labels, parameter_m, color=colors, width=0.58)
    axes[0].set_ylabel('参数量 / M')
    axes[0].set_title('模型参数量')
    for index, value in enumerate(parameter_m):
        axes[0].text(index, value + 1.5, f'{value:.1f}', ha='center')

    axes[1].bar(labels, parameter_mb, color=colors, width=0.58)
    axes[1].set_ylabel('参数张量显存 / MiB')
    axes[1].set_title('参数静态显存')
    for index, value in enumerate(parameter_mb):
        axes[1].text(index, value + 5, f'{value:.0f}', ha='center')
    for axis in axes:
        axis.grid(axis='x', visible=False)
    save_figure(fig, output_dir, 'fig05_model_complexity')


def figure_requirement_matrix(output_dir):
    rows = [
        ('运行环境与 CUDA 可用', 2),
        ('已有视频推理链路', 2),
        ('两条路线同屏对照', 2),
        ('Top-1 / Top-5 展示', 2),
        ('吞吐与时延记录', 2),
        ('UCF101 数据与 101 类', 0),
        ('同预算朴素 3D 基线训练', 0),
        ('相对基线提升 ≥4 个百分点', 0),
        ('训练峰值显存 ≤2 GB', 0),
        ('采样策略三组消融', 1),
        ('至少 3 个训练随机种子', 0),
        ('错误归因与混淆矩阵', 0),
    ]
    values = np.array([[value] for _, value in rows])
    cmap = ListedColormap(['#C95A58', '#D9A441', '#4D9B78'])
    fig, axis = plt.subplots(figsize=(8.8, 5.2), constrained_layout=True)
    axis.imshow(values, cmap=cmap, vmin=0, vmax=2, aspect='auto')
    axis.set_xticks([])
    axis.set_yticks(
        np.arange(len(rows)), [label for label, _ in rows])
    axis.grid(False)
    for spine in axis.spines.values():
        spine.set_visible(False)
    for index, (_, value) in enumerate(rows):
        axis.text(
            0, index,
            {0: '未完成', 1: '部分完成', 2: '已验证'}[value],
            ha='center', va='center', color='white', fontsize=9,
            fontweight='bold')
    axis.set_title('A11 题目要求完成度（运行验证 ≠ 正式实验）')
    axis.tick_params(axis='y', length=0)
    save_figure(fig, output_dir, 'fig06_requirement_matrix')


def write_figure_notes(output_dir, experiment_dir):
    text = f"""# 论文图表说明

数据来源：`{experiment_dir.as_posix()}`。

## fig01_latency_throughput

左右两图分别展示端到端单视频推理耗时和吞吐。该指标包含视频解码、预处理、模型前向与后处理，
不是纯网络 FLOPs 比较。适合放在“系统性能”或“运行验证”小节。

## fig02_top1_confidence

展示两条路线在各测试视频上的 Top-1 标签和置信度。该图只能说明演示模型输出差异，
不能表示 UCF101 分类准确率。建议仅用于方法演示或负结果分析。

## fig03_confidence_delta

展示 TSN-2D 与 R(2+1)D-3D 的 Top-1 置信度差，并标记 Top-1 是否一致。
可用于说明两条路线的错误模式差异，但样本量不足，不能作统计显著性结论。

## fig04_repeat_latency

展示三次重复运行的时延中位数及最小–最大范围。重复的是推理过程，不是训练随机种子。

## fig05_model_complexity

比较模型参数量和参数张量显存。R(2+1)D 参数量明显更大，但当前 GPU 峰值指标是两个
模型同时驻留后的进程峰值，不能解释为单路线训练显存。

## fig06_requirement_matrix

题目要求完成度审计。绿色为已验证，黄色为部分完成，红色为未完成。论文中不应把前三项
运行能力写成核心模型实验已经完成。

## 使用边界

当前所有权重均为 Kinetics-400 预训练演示权重。尚未准备 UCF101 数据和 101 类训练，
因此不能宣称“相对同预算朴素 3D-CNN 提升至少 4 个百分点”，也不能宣称训练峰值低于 2 GB。
"""
    (output_dir / 'PAPER_FIGURE_NOTES.md').write_text(text, encoding='utf-8')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate paper-ready figures from batch experiment output.')
    parser.add_argument('--experiment-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path)
    return parser.parse_args()


def main():
    args = parse_args()
    experiment_dir = args.experiment_dir.resolve()
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir else experiment_dir / 'figures')
    output_dir.mkdir(parents=True, exist_ok=True)
    configure_fonts()

    summary = read_csv(experiment_dir / 'summary.csv')
    for row in summary:
        numeric(row, 'top1_score_mean')
        numeric(row, 'latency_median_seconds')
        numeric(row, 'latency_min_seconds')
        numeric(row, 'latency_max_seconds')
        numeric(
            row, 'throughput_median_videos_per_second')
        numeric(row, 'parameters_million')
        numeric(row, 'parameter_mb')

    figure_latency_throughput(summary, output_dir)
    figure_top1_confidence(summary, output_dir)
    figure_confidence_delta(summary, output_dir)
    figure_repeat_stability(summary, output_dir)
    figure_model_complexity(summary, output_dir)
    figure_requirement_matrix(output_dir)
    write_figure_notes(output_dir, experiment_dir)

    print(json.dumps({
        'experiment_dir': str(experiment_dir),
        'figure_dir': str(output_dir),
        'figures': sorted(path.name for path in output_dir.glob('*.png')),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
