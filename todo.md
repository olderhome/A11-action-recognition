# 待办事项

- [x] 1. 赛题分析与建模设计 - `2analysis-modeling`
  - [x] 固化实验协议、指标与公平比较规则
  - [x] 核实 UCF101 数据来源和显存预算
  - [x] 完成 `reports/ANALYSIS_MODELING_REPORT.md`
- [x] 2. 编程实现和图表生成 - `3coding-visual`
  - [x] 准备 UCF101 与官方 split 1
    - [x] 定位 ZIP 分片损坏范围
    - [x] 补齐缺失或大小错误视频
    - [x] 逐文件校验 13320 个 AVI
    - [x] 构建官方 split 1 与验证集清单
  - [x] 同预算朴素 3D-CNN 基线
  - [x] TSN-2D 与轻量 R(2+1)D 路线
  - [x] 三随机种子正式训练
  - [x] 均匀/稠密/自适应采样消融
  - [x] AMP/梯度检查点/梯度累积消融
  - [x] 时间/空间/均衡预算对照
  - [x] 错误归因与混淆矩阵
  - [x] 输出 `reports/RESULTS_REPORT.md` 和论文图
- [x] 3. 流程与架构图绘制 - `4drawio`
  - [x] 技术路线图
  - [x] 模型结构图
  - [x] 实验流程图
  - [x] 导出 DrawIO 和 PDF
- [x] 4. 技术报告撰写 - `5writing`
  - [x] 5000–8000 字中文报告
  - [x] 图表、结果和参考文献
  - [x] 编译为 PDF
- [x] 5. 演示与答辩材料
  - [x] 现场演示入口
  - [x] 10 分钟答辩 PPT
  - [ ] 5 分钟演示视频或脚本（可选，现场演示已可用）
- [x] 6. 验证和验收 - `6verity`
  - [x] 数值一致性、图表引用、可复现性检查
  - [x] 提交清单和 `reports/VERIFY_REPORT.md`

## 当前执行检查点

- [x] 审计历史演示结果，确认其不能替代正式 UCF101 实验
- [x] 锁定主实验、采样、时空预算和多种子口径
- [x] 将主实验分辨率对齐为 112×112
- [x] 将时间/空间预算改成相同帧像素成本
- [x] 增加特征提取阶段 2 GiB 显存硬性检查
- [x] 完成全量正式实验并核对 2 GiB 约束
- [x] 完成技术论文 PDF
- [x] 完成可编辑答辩 PPTX

## 最终交付文件

- `deliverables/A11_技术论文.pdf`
- `deliverables/A11_答辩汇报_答辩版.pptx`
- `paper/main.typ`
- `reports/RESULTS_REPORT.md`
- `reports/VERIFY_REPORT.md`
