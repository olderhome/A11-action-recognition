# A11 运行验证批量实验

- 运行时间：2026-11-26T11:46:02
- 重复次数：3
- 测试视频数：6
- 模型：Kinetics-400 预训练演示权重

## 汇总

| 用例 | 路线 | Top-1 | 置信度 | 耗时中位数 | 吞吐 | Top-5 校验 | 两模型 GPU 峰值 | Top-1 稳定 |
|---|---|---|---:|---:|---:|---|---:|---|
| 掰手腕示例 | TSN ResNet-50 | arm wrestling | 100.00% | 0.335 s | 2.98 video/s | 未知 | 437 MiB | 是 |
| 掰手腕示例 | R(2+1)D ResNet-34 | arm wrestling | 100.00% | 0.235 s | 4.26 video/s | 未知 | 437 MiB | 是 |
| UCF101 射箭 | TSN ResNet-50 | archery | 99.96% | 0.114 s | 8.76 video/s | 通过 | 437 MiB | 是 |
| UCF101 射箭 | R(2+1)D ResNet-34 | archery | 77.92% | 0.122 s | 8.18 video/s | 通过 | 437 MiB | 是 |
| UCF101 篮球 | TSN ResNet-50 | shooting basketball | 48.96% | 0.112 s | 8.92 video/s | 通过 | 437 MiB | 是 |
| UCF101 篮球 | R(2+1)D ResNet-34 | shooting basketball | 66.15% | 0.121 s | 8.27 video/s | 通过 | 437 MiB | 是 |
| UCF101 弹吉他 | TSN ResNet-50 | playing guitar | 54.92% | 0.120 s | 8.34 video/s | 通过 | 437 MiB | 是 |
| UCF101 弹吉他 | R(2+1)D ResNet-34 | playing guitar | 90.30% | 0.124 s | 8.06 video/s | 通过 | 437 MiB | 是 |
| UCF101 开合跳 | TSN ResNet-50 | stretching arm | 54.74% | 0.112 s | 8.90 video/s | 未知 | 437 MiB | 是 |
| UCF101 开合跳 | R(2+1)D ResNet-34 | dancing gangnam style | 23.46% | 0.125 s | 8.02 video/s | 未知 | 437 MiB | 是 |
| UCF101 足球点球 | TSN ResNet-50 | shooting goal (soccer) | 68.64% | 0.110 s | 9.13 video/s | 通过 | 437 MiB | 是 |
| UCF101 足球点球 | R(2+1)D ResNet-34 | shooting goal (soccer) | 52.44% | 0.116 s | 8.60 video/s | 通过 | 437 MiB | 是 |

## 范围说明

本次实验使用现有短视频和 Kinetics-400 演示权重，验证推理链路、两条路线差异、结果稳定性和吞吐。视频级重复运行不等同于训练随机种子实验；由于尚未准备 UCF101 训练数据与 101 类模型，本结果不能用于验收“相对 3D 基线提升 4 个百分点”或“训练峰值显存不超过 2 GB”。

已知参考标签的用例中：

- TSN ResNet-50：Top-1 准确率 100.0%。
- R(2+1)D ResNet-34：Top-1 准确率 100.0%。
