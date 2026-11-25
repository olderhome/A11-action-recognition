# A11 资源约束下的视频动作识别时空解耦建模

本项目研究 UCF101 上严格显存预算下的视频动作识别。工程包含：

- TSN 式 2D 骨干与时序聚合；
- R3D-18 朴素 3D 基线；
- R(2+1)D-18 轻量 3D 路线；
- 均匀、稠密、自适应采样；
- AMP、梯度检查点与梯度累积显存预检；
- Top-1/Top-5、吞吐、显存与多种子统计；
- 混淆矩阵、分类别召回和代表性错误案例；
- 可在浏览器中操作的两路线视频和摄像头演示。

## 目录

```text
a11code/                   正式数据、特征、训练和图表代码
mmaction2-main/            MMAction2 1.2.0 源码与演示
reports/                   分析、结果、图示和验收报告
figures/                   PNG、PDF 和 DrawIO 源文件
results/validation/        轻量验证结果，不含大模型和特征矩阵
demo/                      少量演示视频和截图
```

UCF101 原始数据、模型 checkpoint、运行时和大型中间特征不进入 Git 仓库。
这些内容应由 `prepare_ucf101.ps1` 和实验脚本按需生成。

## 环境

推荐 Python 3.10/3.11、PyTorch 2.0.1 CUDA 11.8、MMEngine 0.10.7、
MMCV-Lite 2.1.0。

```powershell
python -m pip install torch==2.0.1 torchvision==0.15.2 `
  --index-url https://download.pytorch.org/whl/cu118
python -m pip install -e .\mmaction2-main --no-deps
python -m pip install mmengine==0.10.7 mmcv-lite==2.1.0 `
  opencv-python decord einops matplotlib scipy numpy pandas
```

## UCF101

从 UCF101 官方地址或许可相同的 Kaggle 镜像
`pevogam/ucf101` 获取数据后，将视频放到：

```text
mmaction2-main/data/ucf101/videos/<ClassName>/<video>.avi
```

官方 train/test 文件放到：

```text
mmaction2-main/data/ucf101/annotations/ucfTrainTestlist/
```

然后生成并校验文件清单：

```powershell
python -m a11code.build_manifest
```

数据不会提交到 GitHub，避免数 GB 流量和仓库膨胀。

## 运行

### 浏览器演示

```powershell
powershell -ExecutionPolicy Bypass -File .\run_comparison_app.ps1
```

打开 `http://127.0.0.1:7860`。

### 两路线批量验证

```powershell
powershell -ExecutionPolicy Bypass -File .\run_batch_experiment.ps1
```

### 2 GB 显存预检

```powershell
python -m a11code.run_memory_matrix
```

### 路线、采样和时空预算实验

```powershell
python -m a11code.run_feature_pipeline --suite all
```

### 结果与图表

```powershell
python -m a11code.summarize_results `
  --matrix results/feature_pipeline/.../matrix.json `
  --output-dir results/summary
python -m a11code.plot_feature_results `
  --matrix results/feature_pipeline/.../matrix.json `
  --output-dir figures
```

## 提交边界

仓库只保存代码、配置、文档、图表、CSV/JSON 汇总和少量演示素材。
以下内容不提交：

- UCF101 视频和抽帧；
- 预训练 checkpoint 和训练得到的 `.pth`；
- 大型 `.npy` 特征矩阵；
- Python 运行时和安装缓存；
- 临时下载分片、日志和完整实验缓存。

这些文件可通过 README、固定随机种子和脚本重建。

