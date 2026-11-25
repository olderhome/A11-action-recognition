#set document(
  title: "资源约束下的视频动作识别时空解耦建模",
  author: "Trauma",
)
#set page(
  paper: "a4",
  margin: (x: 2.2cm, top: 2.4cm, bottom: 2.2cm),
  numbering: "1",
  footer: context [
    #set text(size: 9pt, fill: rgb("#6f7378"))
    #h(1fr)
    #counter(page).display("1")
  ],
)
#set text(
  font: ("Microsoft YaHei", "SimSun"),
  size: 10.5pt,
  lang: "zh",
  fill: rgb("#1c2024"),
)
#set par(justify: true, leading: 0.9em)
#set heading(numbering: "1.1")
#show heading.where(level: 1): set text(
  size: 16pt,
  weight: "bold",
  fill: rgb("#14213D"),
)
#show heading.where(level: 2): set text(
  size: 13pt,
  weight: "bold",
  fill: rgb("#276a67"),
)
#show heading.where(level: 3): set text(size: 11pt, weight: "bold")
#set math.equation(numbering: "(1)")
#show figure.caption: set text(size: 9pt, fill: rgb("#555b60"))
#show table.cell.where(y: 0): set text(weight: "bold")
#set table(stroke: 0.45pt + rgb("#c8ccd0"), inset: 5pt)

#align(center)[
  #v(1.2cm)
  #text(size: 23pt, weight: "bold", fill: rgb("#14213D"))[
    资源约束下的视频动作识别
    #linebreak()
    时空解耦建模
  ]
  #v(0.7cm)
  #text(size: 13pt, fill: rgb("#4c555d"))[
    UCF101 · 101 类 · 训练显存不超过 2 GiB
  ]
  #v(0.45cm)
  #line(length: 4cm, stroke: 2pt + rgb("#C66A31"))
  #v(0.45cm)
  #text(size: 10.5pt, fill: rgb("#666b70"))[技术研究报告 · 2026 年 11 月]
]

#v(1.1cm)

#heading(numbering: none, outlined: false)[摘要]

#text(weight: "bold")[
本文研究 UCF101 上训练显存不超过 2 GiB 的视频动作识别时空建模路线。
]
数据采用官方 split 1，训练、验证和测试严格按 group 隔离。方法比较 TSN 式二维骨干时序聚合、朴素 R3D-18 与轻量 R(2+1)D-18，并单独消融均匀、稠密、运动自适应采样以及等成本时间与空间预算。所有核心头部配置使用 3 个训练种子，同时记录 CUDA allocated 与 reserved 峰值。

结果显示，R(2+1)D-18 取得最高 Top-1 83.97%，TSN 时序注意力达到 82.70%，朴素 R3D-18 为 76.37%。两种候选相对基线分别提升 6.34 和 7.60 个百分点，达到题目要求。连续稠密采样比均匀分段低 4.10 个百分点。自适应采样准确率接近均匀采样，但吞吐下降约 68%。等帧像素成本下，空间优先达到 84.19%，时间优先只有 61.71%。因此，在本实验的 2 GiB 冻结主干协议下，应优先投入空间分辨率，并按应用场景在二维高吞吐路线与轻量三维高精度路线之间选择。

#text(weight: "bold")[关键词：]视频动作识别；UCF101；时空解耦；帧采样；显存预算；轻量 3D 卷积

#pagebreak()

#outline(title: [目录], depth: 2)

#pagebreak()

= 问题重述与研究目标

== 研究背景

视频动作识别需要在连续图像中发现具有判别力的空间外观与时间运动模式。与单帧图像分类相比，视频模型还必须处理帧数、运动跨度、背景变化、遮挡和长动作阶段缺失等问题。高容量三维卷积能够直接建模时空联合关系，但其激活和参数规模通常较大；二维骨干结合时序聚合可以复用成熟的图像预训练权重，并通过共享空间编码器降低单帧计算成本。

本课题在 UCF101 的 101 类动作数据上，限定训练阶段 CUDA 显存峰值不超过 2 GiB，研究在有限资源下如何分配空间分辨率、时间长度和模型容量。课题不是简单追求最高精度，而是在同一数据划分、输入预算和评估协议下比较不同时空建模路线，并给出可复核的效率结论。

== 研究问题

题目包含四项相互关联的研究内容。

+ *路线对照。* 比较二维骨干加时序聚合与轻量三维卷积。二维路线采用 TSN 式分段采样，在共享空间编码器上提取每一帧的特征，再用平均池化或时序注意力得到视频表示；三维路线采用 R3D-18 作为朴素基线，并采用 R(2+1)D-18 作为轻量对照。
+ *帧采样消融。* 固定 TSN-2D、8 帧、112×112 和分类头设置，比较均匀、稠密和运动自适应采样，记录额外解码和评分耗时。
+ *显存优化。* 应用 AMP、梯度检查点和梯度累积，同时记录 allocated 与 reserved 峰值，二者都不超过 2048 MiB 才视为满足预算。
+ *错误归因与优先级。* 生成 101 类混淆矩阵、分类别召回、动作语义组准确率，并依据等成本时间/空间实验回答低显存下应优先投入时间维还是空间维。

== 验收指标

主指标为官方测试集 3783 个视频上的视频级 Top-1，辅助指标为 Top-5。候选路线相对同预算 R3D-18 的绝对提升不少于 4 个百分点。每个核心头部配置使用种子 0、1、2，报告均值、样本标准差和同种子配对差值。若目标未达到，须保留负结果并分析原因。

= 数据与实验协议

== 数据完整性

UCF101 共包含 101 类、13320 个视频。原始压缩包存在局部损坏，下载后对每个成员进行恢复和校验。最终 13320 个 AVI 全部存在，类别目录为 101 个，与参考清单相比缺失数为 0、大小不一致数为 0，逐文件首帧解码失败数为 0。

== 官方切分

主实验使用官方 split 1，训练集 9537 个视频，测试集 3783 个视频。为选择训练轮次，从官方训练集中按类别固定留出两个 group 作为验证集，共 1061 个视频，剩余 8476 个视频用于拟合。设三个集合的 group 集合分别为 $G_("fit")$、$G_("val")$、$G_("test")$，则

$ G_("fit") inter G_("val") = G_("fit") inter G_("test") = G_("val") inter G_("test") = emptyset. $

实际检查的三个交集大小均为 0。测试集只用于最终报告，不参与头部轮次选择。

== 预训练与比较口径

三种主路线均使用 Kinetics-400 预训练信息。TSN-2D 使用 ResNet-50 二维骨干，R3D-18 与 R(2+1)D-18 使用对应的 Kinetics-400 三维权重。主实验冻结预训练主干，只训练视频级分类头或时序聚合头。因此本文将其准确表述为“冻结主干迁移训练”，不称为端到端全网络微调。

主对照统一为 8 帧、112×112、101 类输出、官方 split 1 和相同验证 group。批大小依据各模型的显存预检独立选择，最终以实测 2 GiB 硬门禁为准。

#figure(
  table(
    columns: (1.1fr, 1fr, 1.6fr, 0.9fr),
    table.header[路线][主干][时序表示][预训练],
    [TSN-2D], [ResNet-50], [逐帧特征与均值/时序注意力], [Kinetics-400],
    [朴素 3D], [R3D-18], [三维联合卷积与全局池化], [Kinetics-400],
    [轻量 3D], [R(2+1)D-18], [空间/时间分解卷积与全局池化], [Kinetics-400],
  ),
  caption: [主实验配置],
) <main-protocol>

= 模型假设与符号说明

== 基本假设

+ UCF101 官方标签和 split 1 是真实动作标签与权威评估边界；修复文件须与参考清单大小、CRC 和可解码性一致。
+ 同一 group 中视频可能共享演员、场景或拍摄条件，因此训练、验证与测试按 group 隔离。
+ Kinetics-400 预训练知识可以迁移到 UCF101；冻结主干后的特征视为固定视频表示，头部学习 UCF101 决策边界。
+ 视频级概率由同一视频的输入片段或帧特征聚合得到，测试时不做标签相关筛选。
+ 显存预算以 PyTorch CUDA allocator 为测量边界，同时采用 allocated 与 reserved 峰值。
+ 三个训练种子改变头部初始化、优化顺序和训练采样抖动；冻结特征实验的种子差异不能写成端到端模型种子差异。

== 符号

#figure(
  table(
    columns: (auto, 1fr),
    table.header[符号][含义],
    [$K$], [输入帧数],
    [$H, W$], [空间输入高和宽],
    [$x_k$], [第 $k$ 个采样帧],
    [$z_k$], [第 $k$ 帧空间特征],
    [$q_v$], [视频 $v$ 的聚合表示],
    [$p_theta(y|v)$], [视频级类别概率],
    [$M_a(t), M_r(t)$], [allocated/reserved 显存],
    [$A_1, A_5$], [Top-1 与 Top-5],
    [$Delta A$], [相对基线绝对百分点差],
  ),
  caption: [主要符号],
) <symbols>

= 时空解耦模型

#figure(
  image("../figures/fig_model.pdf", width: 96%),
  caption: [三条候选路线与头部结构],
) <route-model>

== TSN 式二维时序聚合

将视频时间轴等分为 $K$ 段，在第 $k$ 段采样一帧 $x_k$。所有帧共享同一空间编码器 $F_(2D)$：

$ z_k = F_(2D)(x_k; theta_(2D)), quad k=1, dots, K. $

平均池化路线为

$ q_v = 1/K sum_(k=1)^K z_k, quad p_theta(y|v) = "softmax"(W q_v + b). $

时序注意力头把 $z_k$ 映射到 $d=256$ 的隐空间并加入可学习位置编码，再经过 Transformer 编码器。位置编码使模型区分动作阶段顺序，而不只对无序帧集合聚合。

== 朴素三维卷积基线

朴素基线将 $K$ 帧作为
$X in bb(R)^(B times 3 times K times H times W)$
输入 R3D-18，通过三维卷积核直接联合学习空间和时间模式：

$ p_theta(y|v) = "softmax"(W "GAP"("R3D"(X; theta_(3D))) + b). $

== 轻量时空分解卷积

R(2+1)D 把三维卷积近似分解为空间二维卷积和时间一维卷积：

$ "Conv"_(3 times 3 times 3) approx "Conv"_(1 times 3 times 3) compose "Conv"_(3 times 1 times 1). $

分解减少单个三维卷积的时空耦合，使空间外观与时间运动可以在中间层分别建模。

== 训练目标

三种路线均使用多类交叉熵：

$ cal(L)(theta) = -1/N sum_(i=1)^N sum_(c=1)^(101) bb(1)(y_i=c) log p_theta(c|v_i). $

头部使用 AdamW、余弦退火和 80 轮训练。验证集按 Top-1 选最佳轮次，最终只在该轮次评估官方测试集。

= 资源约束与帧采样

== 双峰值显存门禁

每个训练或提取配置同时监测
$M_max = max_t M_a(t)$ 与
$R_max = max_t M_r(t)$。可行条件为

$ "feasible" = bb(1)[M_max <= 2048 "MiB" and R_max <= 2048 "MiB"]. $

任何峰值超过预算的进程立即终止，其精度结果不进入可行方案。

== 三种采样

均匀采样把视频分为 $K$ 段，在每段中心附近取样。稠密采样在连续窗口中每隔 $d$ 帧取一帧，能保留短时动作，但可能遗漏长视频的其他阶段。自适应采样先均匀解码 32 个候选帧，计算灰度帧差运动强度

$ m_t = 1/(H W) ||I_(t+1)-I_t||_1, $

再用“运动强度 + 时间多样性”的贪心目标选择 $K$ 帧。额外解码与评分时间单列为 $T_d$ 和 $T_s$。

== 显存优化

AMP 在前向和反向中使用 FP16 计算并保留 FP32 主权重和损失缩放。梯度检查点保存模块边界，在反向时重算中间激活。资源不足时用 $B_("eff") = B_s G$ 表示小批量与梯度累积的有效批量。

== 等成本时间与空间

时间优先和空间优先保持
$K_t H_t W_t = K_s H_s W_s$。时间优先为 16×64×64，空间优先为 4×128×128，二者均处理 65536 个空间像素帧，批大小同为 8；均衡配置为 8×112×112。

= 正式实验结果

== 三条主路线

#figure(
  table(
    columns: (1.35fr, 1.05fr, 1fr, 0.8fr, 0.95fr),
    table.header[路线][Top-1][Top-5][头部峰值][特征吞吐],
    [R3D-18 基线], [76.37±0.30%], [94.48±0.08%], [62 MiB], [32.34 video/s],
    [TSN-2D 线性], [81.29±0.64%], [95.89±0.19%], [146 MiB], [52.98 video/s],
    [TSN-2D 时序注意力], [82.70±0.54%], [95.32±0.60%], [990 MiB], [52.98 video/s],
    [R(2+1)D-18], [83.97±0.26%], [96.22±0.19%], [62 MiB], [22.20 video/s],
  ),
  caption: [三条主路线的正式结果],
) <main-results>

TSN 线性头达到 81.29%，时序注意力提高到 82.70%。R(2+1)D-18 取得最高 Top-1 83.97%，但特征提取吞吐为 22.20 video/s，明显低于 TSN 的 52.98 video/s。R3D-18 的吞吐居中，Top-1 只有 76.37%。

#figure(
  image("../figures/main_route_accuracy.pdf", width: 90%),
  caption: [主路线的 Top-1 与 Top-5],
) <main-accuracy>

同种子配对比较中，TSN 线性头相对 R3D 提升 4.93 个百分点，TSN 时序注意力提升 6.34 个百分点，R(2+1)D-18 提升 7.60 个百分点。三组提升都超过 4 个百分点，对应配对 $t$ 检验 $p$ 值分别为 0.0034、0.0038 和 0.0003。由于只有三个种子，本文不将其解释为大样本意义上的普遍显著性。

#figure(
  image("../figures/main_delta_vs_r3d.pdf", width: 78%),
  caption: [候选路线相对 R3D-18 的绝对 Top-1 提升],
) <main-delta>

== 采样策略消融

#figure(
  image("../figures/sampling_comparison.pdf", width: 90%),
  caption: [采样策略的 Top-1 对比],
) <sampling-results>

固定模型和输入成本后，均匀时序头为 82.70%，连续稠密下降到 78.60%，运动自适为 82.02%。稠密采样只覆盖短时间窗，容易遗漏长视频的其他动作阶段。自适应采样对 3783 个测试视频共解码 121056 个候选帧，测试集评分耗时 196.30 秒，吞吐由 52.98 降至 16.84 video/s。其收益不足以抵消额外预处理成本。

#figure(
  table(
    columns: (1fr, 1fr, 1fr, 1.1fr, 1fr),
    table.header[策略][Top-1][Top-5][吞吐][评分时间],
    [均匀分段], [82.70±0.54%], [95.32±0.60%], [52.98], [0 s],
    [连续稠密], [78.60±0.27%], [93.82±0.06%], [56.23], [0 s],
    [运动自适应], [82.02±0.46%], [94.77±0.21%], [16.84], [196.30 s],
  ),
  caption: [采样策略准确率与端到端成本],
) <sampling-table>

== 显存优化

#figure(
  image("../figures/memory_efficiency.pdf", width: 98%),
  caption: [AMP 与梯度检查点的显存峰值],
) <memory-results>

TSN 的 FP32 reserved 峰值为 950 MiB，AMP 降至 610 MiB，再加入梯度检查点后降至 428 MiB。R3D-18 从 FP32 的 692 MiB 降至 AMP 的 518 MiB；R(2+1)D-18 从 834 MiB 降至 542 MiB。正式时间优先时序头的峰值为 1912 MiB，仍低于 2048 MiB。

== 时间与空间投入优先级

#figure(
  image("../figures/time_space_budget.pdf", width: 86%),
  caption: [等成本条件下的时间与空间优先结果],
) <budget-results>

在每视频 65536 个空间像素帧的等成本条件下，16 帧低分辨率的时序头只有 61.71%，而 4 帧高分辨率的时序头达到 84.19%。空间优先高 22.48 个百分点，同时特征提取 reserved 更低、吞吐更高。结果支持优先投入空间分辨率。时间维并非无效，TSN 时序注意力相对平均池化仍有约 1.41 个百分点收益，但增加帧数必须保持足够空间细节。

#figure(
  table(
    columns: (1.2fr, 1fr, 1fr, 1fr, 1fr),
    table.header[配置][输入][Top-1][特征峰值][吞吐],
    [时间优先], [16×64×64], [61.71±0.37%], [298 MiB], [48.68],
    [空间优先], [4×128×128], [84.19±0.10%], [246 MiB], [71.22],
    [均衡], [8×112×112], [82.70±0.54%], [266 MiB], [52.98],
  ),
  caption: [时间与空间预算对照],
) <budget-table>

= 类别错误归因

采用 R(2+1)D-18 种子 0 的官方测试预测生成 101×101 混淆矩阵。按动作语义分为人际交互、人体动作、物体交互、演奏乐器和体育运动五组，该分组仅用于解释错误结构。

#figure(
  image("../results/feature_pipeline/main_20261125_193324/error_analysis/r2plus1d18/confusion_matrix.pdf", width: 72%),
  caption: [R(2+1)D-18 的 101 类归一化混淆矩阵],
) <confusion>

主要混淆对包括 BrushingTeeth 与 ShavingBeard，YoYo 与 Archery/JugglingBalls，BoxingPunchingBag 与 BoxingSpeedBag，FrontCrawl 与 BreastStroke，以及 CricketShot 与 CricketBowling。它们分别对应面部近景、细长物体轨迹、相近运动场地与相似周期动作。

#figure(
  image("../results/feature_pipeline/main_20261125_193324/error_analysis/r2plus1d18/action_group_accuracy.pdf", width: 86%),
  caption: [动作语义组的测试准确率],
) <action-groups>

人体动作组只有 67.78%，明显低于演奏乐器的 94.76% 和人际交互的 92.05%。最低回类别为 YoYo、Lunges、HandstandWalking、Hammering 和 CricketBowling。错误说明，当背景相近或动作差异只集中在短时阶段时，8 帧全局表示仍会丢失关键时间细节。

= 模型评价与结论

== 题目完成情况

本项目已在 UCF101 官方测试集完成三条路线、三种采样和等成本时间空间配置。核心配置均使用三个训练种子。三种候选的 Top-1 相对 R3D-18 分别提升 4.93、6.34 和 7.60 个百分点，均达到至少 4 个百分点的目标。正式训练和提取均执行 2 GiB 硬门禁。

== 主要结论

+ 低显存下轻量时空分解卷积价值显著。R(2+1)D-18 取得 83.97% 的最高 Top-1，特征提取 reserved 为 218 MiB。
+ 二维时序路线更均衡。TSN 特征提取吞吐为 52.98 video/s，Top-1 达到 82.70%，适合高吞吐场景。
+ 均匀分段优于连续稠密。稠密采样固定 8 帧时比均匀低 4.10 个百分点。
+ 自适应采样没有正收益。它接近均匀精度，但额外候选帧评分使吞吐下降约 68%。
+ 等成本下应优先空间分辨率。空间优先比时间优先高 22.48 个百分点。

== 局限与改进

主实验冻结预训练主干，只训练分类头或时序聚合头，因此结论不等同于全网络端到端微调。自适应采样仅使用灰度帧差，后续可替换为轻量光流、帧级显著性或多尺度候选窗口。三维路线精度最高但吞吐较低，可继续研究时序蒸馏和通道剪枝。人体动作组和细粒度周期动作仍是主要短板。

== 推广

“双峰值显存门禁、固定输入成本、同种子配对比较、额外预处理成本单列”的框架可推广到课堂行为识别、工业操作合规检测、体育动作分析和跌倒监测。二维路线适合在线推断，轻量三维路线适合事件完成后的高精度复核。

= 参考文献

+ Wang L, Xiong Y, Wang Z, et al. Temporal segment networks: Towards good practices for deep action recognition. ECCV, 2016: 20–36.
+ Carreira J, Zisserman A. Quo vadis, action recognition? A new model and the Kinetics dataset. CVPR, 2017: 6299–6308.
+ Soomro K, Zamir A R, Shah M. UCF101: A dataset of 101 human action classes from videos in the wild. CRCV-TR-12-01, 2012.
+ Tran D, Wang H, Torresani L, et al. A closer look at spatiotemporal convolutions for action recognition. CVPR, 2018: 6450–6459.
+ Kay W, Carreira J, Simonyan K, et al. The Kinetics human action video dataset. arXiv:1705.06950, 2017.
+ Micikevicius P, Narang S, Alben J, et al. Mixed precision training. ICLR, 2018.
+ Chen T, Xu B, Zhang C, et al. Training deep nets with sublinear memory cost. arXiv:1604.06174, 2016.
+ Loshchilov I, Hutter F. Decoupled weight decay regularization. ICLR, 2019.

= 附录：核心实现

```python
peak_allocated = torch.cuda.max_memory_allocated() / (1024**2)
peak_reserved = torch.cuda.max_memory_reserved() / (1024**2)
if peak_allocated > 2048 or peak_reserved > 2048:
    raise RuntimeError("2 GiB memory budget exceeded")
```

```python
value = self.projection(features)
value = value + self.position[:, :value.shape[1]]
value = self.encoder(value)
value = self.norm(value.mean(dim=1))
logits = self.classifier(value)
```

完整代码、主结果矩阵、分类别指标和错误案例位于项目仓库。
