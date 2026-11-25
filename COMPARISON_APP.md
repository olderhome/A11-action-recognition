# A11 时空路线对照测试台

## 启动

在本目录运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_comparison_app.ps1
```

脚本会在后台启动本地服务，并打开：

```text
http://127.0.0.1:7860
```

关闭后台服务：

```powershell
powershell -ExecutionPolicy Bypass -File .\stop_comparison_app.ps1
```

## 批量实验

按 3 次重复自动运行页面内全部测试视频，并生成 CSV、JSON 和 Markdown 报告：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_batch_experiment.ps1
```

结果保存在 `outputs/experiments/<运行时间>/`，其中 `REPORT.md` 是便于查看的汇总。

根据最近一次批量实验生成论文候选图表：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_review_figures.ps1
```

图表会保存到 `outputs/review_<日期>/figures/`，同时生成 PNG 和 PDF。

## 页面可以做什么

- 运行“掰手腕示例”和已有的“摄像头人物近景”测试用例；
- 点击“采集摄像头并测试”，采集 4 秒摄像头视频后自动对照；
- 同屏比较 TSN ResNet-50 的 2D 分段聚合路线与 R(2+1)D ResNet-34 的轻量 3D 路线；
- 在每张画面内显示 Top-1、置信度、推理耗时和后续候选类别；
- 显示两条路线是否给出一致 Top-1、各自参数规模、模型驻留显存和最近运行记录；
- 每次运行自动保存 JSON 到 `outputs/comparison_results/`。

## 当前边界

两个模型目前都是 Kinetics-400 预训练模型，用于验证视频输入、模型推理和可视化链路。
它们还不是 UCF101 的 101 类训练结果；页面显示的显存是推理时两个模型在 GPU 上的驻留量，
不能替代训练阶段的“峰值显存不超过 2 GB”验收。
