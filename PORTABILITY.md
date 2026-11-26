# A11 跨机器运行说明

仓库不包含虚拟环境、模型权重和 UCF101 训练数据。换机后执行一次安装：

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

如果新电脑没有 NVIDIA CUDA 显卡，可安装 CPU 版本用于界面和短视频演示：

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1 -CpuOnly
```

安装脚本会创建 `.venv`、安装依赖、安装本地 MMAction2，并下载演示权重。
如果不希望立即下载权重，可先执行 `-SkipWeights`。

## 启动可视化测试台

```powershell
powershell -ExecutionPolicy Bypass -File .\run_comparison_app.ps1
```

浏览器打开 `http://127.0.0.1:7860`。程序会自动选择 GPU；没有 CUDA 时回退到
CPU。

## 从命令行运行自检

```powershell
powershell -ExecutionPolicy Bypass -File .\run_comparison_app.ps1
powershell -ExecutionPolicy Bypass -File .\run_batch_experiment.ps1
```

## 演示视频

`mmaction2-main/demo/demo.mp4` 是上游演示片段。`demo/test_cases/` 另含 5 个
小型 UCF101 测试片段：射箭、篮球、弹吉他、开合跳和足球点球。它们只用于系统
演示，不参与正式精度评估。

## 正式数据

UCF101 完整数据不属于 Git 仓库。正式复现需按 `README.md` 准备数据，并另行运行
实验脚本。数据、权重、特征和运行环境都在 `.gitignore` 中排除。
