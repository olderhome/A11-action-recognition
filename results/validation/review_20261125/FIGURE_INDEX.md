# 论文图表索引

## 本次可用图表

| 文件 | 用途 | 论文位置建议 |
|---|---|---|
| `figures/fig01_latency_throughput.png/pdf` | 端到端时延与吞吐 | 系统性能、演示实验 |
| `figures/fig02_top1_confidence.png/pdf` | 两条路线 Top-1 标签与置信度 | 路线行为差异、负结果 |
| `figures/fig03_confidence_delta.png/pdf` | 路线间置信度差与一致性 | 错误模式分析 |
| `figures/fig04_repeat_latency.png/pdf` | 三次重复时延波动 | 稳定性附录 |
| `figures/fig05_model_complexity.png/pdf` | 参数量与参数显存 | 模型效率对比 |
| `figures/fig06_requirement_matrix.png/pdf` | 题目完成度审计 | 内部评审，不建议作为论文正文 |

## 截图

| 文件 | 内容 |
|---|---|
| `screenshots/dashboard_running.png` | 两条路线均识别掰手腕的测试台截图 |
| `screenshots/dashboard_route_disagreement.png` | 摄像头片段上 TSN 与 R(2+1)D 标签冲突截图 |

## 使用限制

这些图来自 Kinetics-400 演示模型和 5 个短视频。它们可以支撑“系统实现与运行验证”，
不能支撑 UCF101 精度、同预算提升 4 个百分点或训练显存不超过 2 GB 的论文结论。
正式论文主实验完成后应优先替换 fig01、fig02 和 fig03 的数据。
