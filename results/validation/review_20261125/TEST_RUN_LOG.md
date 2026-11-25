# 复核运行记录

## 环境

- 日期：2026-11-25
- Python：便携环境 `runtime/python311/python.exe`
- PyTorch：`2.0.1+cu118`
- CUDA 可用：是
- GPU：NVIDIA GeForce GTX 1050 Ti
- MMAction2：`1.2.0`
- `pip check`：无损坏依赖

## 最终批量运行

命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_batch_experiment.ps1
```

最终结果目录：`outputs/experiments/20261125_121544/`

- 视频数：5
- 重复次数：3
- 两条路线
- 路线评测：30 次
- 总耗时：31.73 秒
- Top-1 标签在三次重复中全部稳定
- 路线 Top-1 一致视频：2/5
- 两模型进程推理峰值：约 437 MiB

## 图表生成

命令：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_review_figures.ps1 `
  -ExperimentDir "C:\Users\Administrator\Desktop\资料\A11题\outputs\experiments\20261125_121544"
```

生成 6 组 PNG+PDF：

- `fig01_latency_throughput`
- `fig02_top1_confidence`
- `fig03_confidence_delta`
- `fig04_repeat_latency`
- `fig05_model_complexity`
- `fig06_requirement_matrix`

## 页面验证

- `/api/health` 返回 `ok=true`、CUDA 可用
- `/api/testcases` 返回 5 个视频用例
- 页面成功运行“掰手腕示例”
- 页面成功运行“摄像头人物近景”，两条路线给出冲突 Top-1
- 页面截图保存成功

## 结论

运行与可视化链路通过；题目核心实验尚未完成。详见 `REVIEW.md` 和
`REQUIREMENTS_TRACEABILITY.csv`。
