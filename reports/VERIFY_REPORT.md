# 验证和验收报告

## 结论

PASS

项目已完成题目规定的核心对照、采样消融、显存优化、多种子统计和错误归因。
主实验为冻结预训练主干的迁移训练，这一范围已经在论文和答辩材料中明确标注。

## 检查项

| 检查项 | 结果 | 说明 |
| --- | --- | --- |
| UCF101 完整性 | PASS | 13320 个 AVI；101 类；大小错误 0；首帧解码失败 0 |
| 官方切分 | PASS | 9537 训练 / 3783 测试；训练、验证、测试 group 交集均为 0 |
| 主路线 | PASS | TSN-2D、R3D-18、R(2+1)D-18 均完成 |
| 随机种子 | PASS | 核心头部配置均为 3 seeds |
| 4 个百分点目标 | PASS | 三种候选分别提升 4.93、6.34、7.60 个百分点 |
| 2 GiB 约束 | PASS | 正式最高 reserved 为 1912 MiB |
| 采样消融 | PASS | 均匀、稠密、自适应均完成并记录额外成本 |
| 错误归因 | PASS | 混淆矩阵、类别召回、动作组、错误案例均生成 |
| 时空优先级 | PASS | 同帧像素成本下空间优先高 22.48 个百分点 |
| 文本质量门禁 | PASS | `writing_check.sh` 返回 PASS |
| Word 结构检查 | PASS | DOCX 包完整；31 个标题；9 个表格；15 个图片；关键数值齐全 |
| Word 表格几何 | PASS | 9 个表格的 tblW、tblInd、tblGrid 与单元格宽度一致 |
| Word 可访问性 | PASS | 高、中、低问题均为 0 |
| Word 页面渲染 | WARN | 本机没有 Word 或 LibreOffice，未安装新组件；已用结构、样式、图片尺寸和同版式预览核验 |
| PPTX 包结构 | PASS | 12 页，包完整性 0 findings |
| PPTX 版式 | PASS | 0 layout findings，统一使用 Microsoft YaHei |
| PPTX 原生图表 | PASS | 4 个 native chart 与嵌入工作簿校验通过 |
| PPTX 逐页预览 | PASS | 12 页均渲染检查，图片和文字完整 |

## 数值一致性

论文、PPT 和 `reports/RESULTS_REPORT.md` 使用同一正式结果：

- R3D-18：76.37%±0.30%
- TSN-2D 线性：81.29%±0.64%
- TSN-2D 时序注意力：82.70%±0.54%
- R(2+1)D-18：83.97%±0.26%
- 空间优先：84.19%；时间优先：61.71%

所有关键数值可追溯到：

- `results/feature_pipeline/main_20261125_193324/summary/summary.json`
- `results/feature_pipeline/main_20261125_193324/summary/aggregate.csv`
- `results/feature_pipeline/main_20261125_193324/summary/comparisons.csv`
- `results/memory/memory_20261125_210742/matrix.json`

## 论文和 PPT

- Word 论文：`deliverables/A11_技术论文.docx`
- Word 构建脚本：`paper/word-build/build_docx.py`
- 可编辑答辩 PPT：`deliverables/A11_答辩汇报_终版.pptx`
- PPT 预览：`presentation/previews/`

## 适用范围与验证限制

1. 主实验采用冻结预训练主干，而不是端到端全网络微调。该限制已经写入论文、PPT 末页和
   `reports/RESULTS_REPORT.md`。
2. 已提供 5 分钟演示脚本；现场答辩可直接使用现有浏览器测试台和摄像头演示。
3. 本机没有 Microsoft Word 或 LibreOffice，因此未执行 DOCX 的逐页程序渲染。按照用户要求
   没有安装额外软件。Word 文件已通过包完整性、标题层级、图片尺寸、内容占位符和可访问性检查。
