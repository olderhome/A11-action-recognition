# A11 资源约束下的视频动作识别时空解耦建模

## 项目组成

- `mmaction2-main/`：MMAction2 1.2.0 基线与交互式演示。
- `a11code/`：正式 UCF101 数据、训练、特征、消融和错误分析代码。
- `results/`：训练日志、checkpoint、特征和预测结果。
- `figures/`：论文候选图、架构图和路线图。
- `reports/`：分析、结果、图示和验收报告。
- `paper/`：技术报告源文件与内部预览。
- `deliverables/`：可编辑 Word 论文和答辩 PPTX。

## 正式结果

| 路线 | Top-1 | Top-5 |
| --- | ---: | ---: |
| R3D-18 基线 | 76.37±0.30% | 94.48±0.08% |
| TSN-2D 线性 | 81.29±0.64% | 95.89±0.19% |
| TSN-2D 时序注意力 | 82.70±0.54% | 95.32±0.60% |
| R(2+1)D-18 | 83.97±0.26% | 96.22±0.19% |

两种候选相对 R3D-18 分别提升 6.34 和 7.60 个百分点，达到至少 4 个百分点的目标。
正式实验最高 reserved 峰值为 1912 MiB，满足 2 GiB 训练预算。

主实验采用冻结预训练主干的迁移训练，只训练分类头或时序聚合头，不是端到端全网络微调。
完整数据、图表和验收结论见：

- `reports/RESULTS_REPORT.md`
- `reports/VERIFY_REPORT.md`
- `deliverables/A11_技术论文.docx`
- `deliverables/A11_答辩汇报_终版.pptx`

## 环境

第一次在新机器运行时，安装独立环境、依赖和演示权重：

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

无 NVIDIA 显卡时可使用 CPU 演示环境：

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -CpuOnly
```

安装完成后使用：

```powershell
.\.venv\Scripts\python.exe -m pip check
```

已验证：

- Python 3.11
- PyTorch 2.0.1 + CUDA 11.8
- TorchVision 0.15.2
- MMAction2 1.2.0
- NVIDIA GTX 1050 Ti 4 GB

仓库不包含 `.venv`、模型权重或 UCF101 训练数据；这些内容由安装和数据脚本生成。
完整换机步骤见 `PORTABILITY.md`。

## UCF101 准备

官方 split 文件位于：

```text
mmaction2-main/data/ucf101/annotations/ucfTrainTestlist/
```

解压并验证视频：

```powershell
powershell -ExecutionPolicy Bypass -File .\prepare_ucf101.ps1
```

该脚本校验：

- 101 个动作类别；
- 13,320 段视频；
- 官方 split 1 的 9,537 个训练视频和 3,783 个测试视频；
- 训练集与测试集没有共享“类别/group”键。

## 正式实验

类别、group 和文件清单：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m a11code.build_manifest
```

2 GB 显存预检：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m a11code.run_memory_matrix
```

路线、采样和时空预算完整实验（断点可续）：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m a11code.run_feature_pipeline `
  --suite all --seeds 0 1 2 --num-workers 2
```

错误归因：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m a11code.analyze_errors `
  --predictions results/.../predictions.csv `
  --output-dir results/error_analysis
```

## 交互演示

```powershell
powershell -ExecutionPolicy Bypass -File .\run_comparison_app.ps1
```

打开 `http://127.0.0.1:7860`。

仓库内置 5 个小型 UCF101 演示片段，位于 `demo/test_cases/`。这些视频只用于
验证两条路线和界面，不参与正式精度评估。

## 实验原则

- 所有路线使用 UCF101 split 1。
- 比较采用相同帧数、空间尺寸、预训练数据和评价口径。
- 训练头使用至少 3 个随机种子。
- 训练显存同时记录 allocator 已分配和预留峰值，硬上限 2,048 MiB。
- 所有结果、图表和结论必须能追溯到原始日志与预测文件。
