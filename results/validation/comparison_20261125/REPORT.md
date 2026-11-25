# A11 运行验证批量实验

- 运行时间：2026-11-25T12:16:16
- 重复次数：3
- 测试视频数：5
- 模型：Kinetics-400 预训练演示权重

## 汇总

| 用例 | 路线 | Top-1 | 置信度 | 耗时中位数 | 吞吐 | Top-5 校验 | 两模型 GPU 峰值 | Top-1 稳定 |
|---|---|---|---:|---:|---:|---|---:|---|
| 掰手腕示例 | TSN ResNet-50 | arm wrestling | 100.00% | 0.252 s | 3.97 video/s | 通过 | 437 MiB | 是 |
| 掰手腕示例 | R(2+1)D ResNet-34 | arm wrestling | 100.00% | 0.237 s | 4.22 video/s | 通过 | 437 MiB | 是 |
| 摄像头人物近景 | TSN ResNet-50 | beatboxing | 89.71% | 0.174 s | 5.75 video/s | 未知 | 437 MiB | 是 |
| 摄像头人物近景 | R(2+1)D ResNet-34 | smoking | 26.89% | 0.181 s | 5.53 video/s | 未知 | 437 MiB | 是 |
| 新摄像头片段 1 | TSN ResNet-50 | beatboxing | 97.68% | 0.183 s | 5.45 video/s | 未知 | 437 MiB | 是 |
| 新摄像头片段 1 | R(2+1)D ResNet-34 | smoking | 45.90% | 0.185 s | 5.40 video/s | 未知 | 437 MiB | 是 |
| 新摄像头片段 2 | TSN ResNet-50 | beatboxing | 72.43% | 0.181 s | 5.53 video/s | 未知 | 437 MiB | 是 |
| 新摄像头片段 2 | R(2+1)D ResNet-34 | smoking | 59.71% | 0.181 s | 5.53 video/s | 未知 | 437 MiB | 是 |
| 新摄像头片段 3 | TSN ResNet-50 | beatboxing | 83.68% | 0.185 s | 5.41 video/s | 未知 | 437 MiB | 是 |
| 新摄像头片段 3 | R(2+1)D ResNet-34 | beatboxing | 50.65% | 0.196 s | 5.11 video/s | 未知 | 437 MiB | 是 |

## 范围说明

本次实验使用现有短视频和 Kinetics-400 演示权重，验证推理链路、两条路线差异、结果稳定性和吞吐。视频级重复运行不等同于训练随机种子实验；由于尚未准备 UCF101 训练数据与 101 类模型，本结果不能用于验收“相对 3D 基线提升 4 个百分点”或“训练峰值显存不超过 2 GB”。

已知参考标签的用例中：

- TSN ResNet-50：Top-1 准确率 100.0%。
- R(2+1)D ResNet-34：Top-1 准确率 100.0%。
