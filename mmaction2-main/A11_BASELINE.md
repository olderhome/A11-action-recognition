# A11 基线工程说明

## 选定工程

- 工程：OpenMMLab MMAction2
- 上游地址：https://github.com/open-mmlab/mmaction2
- 上游代码版本：`v1.2.0`
- 下载时主分支提交：`a5a167dff2399e2d182a60332325f9c0d4663517`
- 本地基线提交：由“Import MMAction2 v1.2.0 baseline at a5a167d”创建
- 许可证：Apache-2.0
- 源码包 SHA-256：`816915e5ea980e870d55a916ad6d628ca3014f017350f55c0a2b55829fbec16d`

## 选择理由

MMAction2 提供统一的数据集、训练、评估和配置体系，并同时包含本项目需要比较的
2D 时序聚合模型与 3D 卷积模型。官方工程已包含 UCF101 文件列表生成、
TSN/TSM、C3D、R(2+1)D 等实现，便于在相同数据划分、训练器和评价协议下开展受控实验。

## 当前机器的关键限制

- GPU：NVIDIA GeForce GTX 1050 Ti，总显存 4 GB
- 当前 Python：3.14
- 当前 PyTorch：`2.14.1+cpu`，未安装 CUDA 版本

MMAction2 1.2.0 的依赖链通常要求使用独立的 Python 3.10/3.11 环境。后续应先创建
专用虚拟环境，再安装 CUDA 版 PyTorch、MMEngine 与匹配的 MMCV。实验时通过训练期间的
CUDA 显存峰值监测，将可用训练预算控制在 2 GB 以内；显卡总显存为 4 GB 不等于允许使用
4 GB 训练。

## 首批可改造配置

- 2D 时序聚合功能基线：
  `configs/recognition/tsm/tsm_imagenet-pretrained-mobilenetv2_8xb16-1x1x8-100e_kinetics400-rgb.py`
- 轻量 3D 对照：
  `configs/recognition/r2plus1d/r2plus1d_r34_8xb8-8x8x1-180e_kinetics400-rgb.py`
- 3D 朴素基线起点：
  `configs/recognition/c3d/c3d_sports1m-pretrained_8xb30-16x1x1-45e_ucf101-rgb.py`
- UCF101 数据准备：
  `tools/data/ucf101/README_zh-CN.md`

以上配置均需针对单卡、2 GB 峰值显存、UCF101 的 101 类输出和本项目采样策略重新配置。
上游 X3D 模型在当前模型的说明中主要用于测试，暂不作为首个训练基线。

## 版本管理

上游源码已作为本地 Git 的初始基线提交，并添加 `upstream` 远程地址。后续的模型、
采样模块、配置和实验脚本应在独立提交中修改，以便与原始工程对比。
