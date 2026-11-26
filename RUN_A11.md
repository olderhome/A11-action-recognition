# A11 基线运行说明

## 已配置环境

- 便携 Python：`runtime/python311/python.exe`
- PyTorch：`2.0.1+cu118`
- TorchVision：`0.15.2+cu118`
- MMAction2：`1.2.0`
- MMEngine：`0.10.7`
- MMCV-Lite：`2.1.0`
- 显卡：NVIDIA GeForce GTX 1050 Ti

不需要激活系统 Python，运行脚本会直接调用当前目录中的便携 Python。

如果项目被复制到另一台电脑，先运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

脚本会创建 `.venv` 并安装依赖与演示权重。启动脚本会依次寻找
`runtime\python311\python.exe`、`.venv\Scripts\python.exe` 和系统 Python。

## 视频文件演示

在 PowerShell 中运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1
```

演示过程会读取 `mmaction2-main/demo/demo.mp4`，使用 TSN ResNet-50
Kinetics-400 权重进行识别，并在 `outputs/demo_tsn.mp4` 生成带预测标签的结果视频。

也可以直接运行：

```powershell
cd .\mmaction2-main
..\.venv\Scripts\python.exe -X utf8 demo\demo.py `
  demo\demo_configs\tsn_r50_1x1x8_video_infer.py `
  checkpoints\tsn_r50_kinetics400.pth `
  demo\demo.mp4 `
  tools\data\kinetics\label_map_k400.txt `
  --device cuda:0
```

## 摄像头实时演示

在 PowerShell 中运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_webcam.ps1
```

程序会打开摄像头 0，并在窗口中显示实时动作识别结果。按 `q`、`Q` 或 `Esc` 退出。

本机摄像头需要 Windows DirectShow 后端。项目原有的 `webcam_demo.py` 使用默认后端时
无法打开设备，现已修改为在 Windows 上调用 `cv2.CAP_DSHOW`，并增加了摄像头打开失败提示。

## 当前模型范围

当前预训练权重是 Kinetics-400 模型，可识别 400 类常见动作，不是 UCF101 的 101 类模型。
它用于验证运行环境、视频输入和摄像头链路。

正式 A11 实验使用 UCF101 官方 split 1，在冻结的 Kinetics-400 主干上训练
UCF101 分类头或时序聚合头。主实验为 8 帧、112×112，训练种子为 0、1、2；
特征提取和头部训练的 CUDA allocated/reserved 峰值都必须低于 2048 MiB。
这是一套资源受限的迁移训练协议，不应描述为端到端全网络微调。

完整的正式实验与验收顺序：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_full_experiment.ps1
```

脚本会依次校验全量视频、构建官方切分、运行显存矩阵、执行主路线/采样/时空预算
实验、按 3 个种子汇总，并生成论文数据图与错误归因。

`mmcv-lite` 导入时会出现 `MultiScaleDeformableAttention` 不可用的警告。该模块属于部分
Transformer 模型使用的可选算子，不影响当前 TSN、TSM、C3D 和 R(2+1)D 识别演示。
