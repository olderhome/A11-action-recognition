# -*- coding: utf-8 -*-
"""生成课题A11开题报告 Word 文档"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

doc = Document()

# ========== 全局样式设置 ==========
style = doc.styles['Normal']
style.font.name = '宋体'
style.font.size = Pt(12)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
style.paragraph_format.line_spacing = 1.5
style.paragraph_format.first_line_indent = Pt(24)

# 页面设置
for section in doc.sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)

def add_title(text, level=0):
    """添加标题"""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 0 else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.name = '黑体'
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    if level == 0:
        run.font.size = Pt(18)
        run.bold = True
    elif level == 1:
        run.font.size = Pt(15)
        run.bold = True
    elif level == 2:
        run.font.size = Pt(13)
        run.bold = True
    return p

def add_body(text):
    """添加正文段落"""
    p = doc.add_paragraph(text)
    return p

def add_table(headers, rows):
    """添加表格"""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # 表头
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ''
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Pt(0)
        run = p.add_run(h)
        run.bold = True
        run.font.name = '黑体'
        run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
        run.font.size = Pt(11)
    # 数据行
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = ''
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Pt(0)
            run = p.add_run(str(val))
            run.font.name = '宋体'
            run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
            run.font.size = Pt(11)
    doc.add_paragraph()  # 表后空行
    return table

# ========== 封面标题 ==========
add_title('课题开题报告', level=0)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Pt(0)
run = p.add_run('资源约束下的视频动作识别时空解耦建模研究')
run.font.name = '黑体'
run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
run.font.size = Pt(16)
run.bold = True

doc.add_paragraph()

# ========== 一、题目 ==========
add_title('一、题目', level=1)
add_body('资源约束下的视频动作识别时空解耦建模研究（课题编号：A11）')

# ========== 二、研究目标 ==========
add_title('二、研究目标', level=1)
add_body('本课题旨在解决低显存预算条件下视频动作识别模型的精度与效率权衡问题。具体研究目标如下：')
add_body('第一，在 UCF101 数据集上，以不超过 2 GB 显存峰值为硬约束，训练视频动作识别模型，使其 top-1 准确率相对同预算下的朴素 3D-CNN 基线提升不少于 4 个百分点。')
add_body('第二，系统研究帧采样策略（均匀采样、稠密采样、自适应采样）对动作识别准确率的影响，揭示不同采样策略在低显存约束下的适用场景与性能边界。')
add_body('第三，通过实证研究回答核心科学问题：在低显存预算条件下，时间维度建模与空间维度建模哪个更值得投入计算资源，从而给出时空建模优先级的明确结论。')
add_body('第四，建立一套可复现的低显存视频动作识别实验框架，包括数据构造、模型训练、显存监控、消融实验与错误归因分析的完整流程，为后续相关研究提供参考基准。')

# ========== 三、研究内容 ==========
add_title('三、研究内容', level=1)

add_title('3.1 两条技术路线的对照研究', level=2)
add_body('本课题设置两条并行的技术路线，并在完全相同的显存预算下进行公平对比：')
add_body('路线一为 2D 骨干网络与时序聚合相结合的方法。该路线采用 2D 卷积神经网络（如 ResNet-18、ResNet-34）提取单帧空间特征，再通过时序聚合模块（如 TSN 式分段平均池化、时序注意力机制、时序移位模块 TSM 等）对多帧特征进行聚合，形成视频级表示。该路线的优势在于 2D 卷积计算量和显存占用较低，可以在有限显存预算内支持更多输入帧数或更高空间分辨率。')
add_body('路线二为轻量级 3D 卷积方法。该路线直接使用 3D 卷积进行时空联合建模，但通过模型轻量化设计控制显存占用，包括采用深度可分离 3D 卷积（如 X3D 系列）、将 3D 卷积分解为 2D 空间卷积与 1D 时间卷积（如 R(2+1)D）、缩减通道数与网络深度等手段。该路线的优势在于能够直接捕捉时空联合特征，但显存压力较大，需要在 2 GB 约束下仔细配置帧数、分辨率与批量大小。')

add_title('3.2 帧采样策略消融实验', level=2)
add_body('针对视频帧采样策略，本课题设计三种采样方式并进行系统消融：')
add_body('均匀采样：将视频沿时间维度均匀划分为 K 个片段，每个片段随机或等间隔选取一帧，是 TSN 等方法的经典策略，适合长视频的全局覆盖。')
add_body('稠密采样：从视频中连续选取 N 帧，是 3D 卷积网络的常用输入方式，适合捕捉精细的短期运动模式，但在长视频中可能遗漏关键动作阶段。')
add_body('自适应采样：根据视频内容动态选择帧，例如基于帧间像素差异或光流幅度评估运动强度，在运动剧烈的时间段多采样、在静止时间段少采样，以期在相同帧数预算下获得更具信息量的输入。')
add_body('上述三种采样策略将分别与两条技术路线组合，在不同帧数（8 帧、16 帧、32 帧）下进行网格实验，分析采样策略与模型架构之间的匹配关系。')

add_title('3.3 显存优化技术应用与消融', level=2)
add_body('为在 2 GB 显存预算下训练深度模型，本课题应用并系统评估以下显存优化技术：')
add_body('混合精度训练（AMP）：使用 FP16 进行前向计算与梯度存储，同时保留 FP32 主权重，可显著降低显存占用并加速训练。')
add_body('梯度检查点（Gradient Checkpointing）：在前向传播时不保存全部中间激活值，反向传播时重新计算，以计算时间换取显存空间。')
add_body('梯度累积：在小批量大小下通过多步梯度累积模拟大批量训练，保证训练稳定性。')
add_body('输入分辨率与帧数动态调整：在 112×112、160×160、224×224 三档空间分辨率以及 8、16、32 帧三档时间长度下进行显存—精度权衡分析。')
add_body('每项技术将进行独立消融实验，量化其对显存峰值、训练速度与识别准确率的影响。')

add_title('3.4 类别代表性动作的错误归因分析', level=2)
add_body('本课题将对模型的错误进行系统性归因分析：')
add_body('首先，生成 101 类的混淆矩阵，找出最易混淆的类别对，分析混淆原因（如动作相似、背景相似、物体相似等）。')
add_body('其次，按 UCF101 的五大动作类型（体育运动、仅身体运动、演奏乐器、人与物交互、人与人交互）分组计算准确率，分析不同类型动作的识别难度差异。')
add_body('再次，对比两条技术路线的错误模式差异，分析 2D+时序聚合路线与轻量 3D 路线各自擅长和薄弱的动作类型。')
add_body('最后，选取典型错误案例，通过 Grad-CAM 等可视化方法分析模型注意力区域，定性解释错误成因。')

# ========== 四、关键技术 ==========
add_title('四、关键技术', level=1)
add_body('本课题涉及的关键技术包括以下几个方面：')
add_body('视频表示学习：研究如何从视频中提取有效的时空特征表示，包括 2D 卷积空间特征提取、3D 卷积时空联合特征提取、以及多帧特征的时序聚合方法。')
add_body('时空特征解耦：将视频理解中的空间建模与时间建模解耦为独立模块，分别研究其在低显存约束下的最优配置，并分析二者之间的资源分配优先级。')
add_body('模型效率优化：包括混合精度训练、梯度检查点、模型轻量化、输入分辨率与帧数优化等技术，实现在极低显存预算下的深度模型训练。')
add_body('多模态可选扩展：在 RGB 模态基础上，可选择性引入光流模态，构建两流架构，进一步提升识别准确率。光流提取采用 TV-L1 算法，在训练前离线计算并存储。')
add_body('统计检验与可复现性：所有核心实验均设置不少于 3 个随机种子，报告均值与标准差，并采用配对 t 检验验证性能提升的统计显著性，确保结论的可靠性与可复现性。')

# ========== 五、技术路线 ==========
add_title('五、技术路线', level=1)
add_body('本课题的技术路线按以下六个阶段逐步推进：')

add_table(
    ['阶段', '主要工作', '产出物'],
    [
        ['阶段一：数据准备', 'UCF101 数据集下载、视频抽帧、数据预处理、训练/测试划分格式化', '标准化数据集、数据加载器'],
        ['阶段二：基线建立', '实现朴素 3D-CNN 基线、显存 profiling、确定 2 GB 预算下的最大配置、训练基线模型', '基线模型、基线准确率'],
        ['阶段三：两条路线实现', '实现 2D 骨干+时序聚合路线与轻量 3D 卷积路线，各自调优至 2 GB 预算最优', '两条路线模型、对比结果'],
        ['阶段四：采样策略消融', '实现均匀/稠密/自适应三种采样策略，进行网格实验与分析', '消融实验结果、采样策略分析报告'],
        ['阶段五：效率优化与归因', '显存优化技术消融、时空投入对比实验、混淆矩阵与错误归因分析', '优化消融结果、错误归因报告'],
        ['阶段六：报告撰写', '整理全部实验结果、撰写技术报告、准备答辩材料', '技术报告、汇报 PPT、演示视频'],
    ]
)

add_body('在阶段五中，时空投入对比实验是回答核心科学问题的关键。该实验固定显存预算为 2 GB，对比三种资源分配方式：时间优先配置（高帧数、低分辨率）、空间优先配置（低帧数、高分辨率）、均衡配置（中等帧数与分辨率），通过比较三种配置的 top-1 准确率，得出时间维与空间维的投入优先级结论。')

# ========== 六、数据来源 ==========
add_title('六、数据来源', level=1)
add_body('本课题使用 UCF101 数据集，该数据集由中佛罗里达大学计算机视觉研究中心（CRCV）于 2012 年发布，是视频动作识别领域最经典的基准数据集之一。数据集可从官方网站公开下载，仅限学术研究用途。')
add_body('UCF101 数据集包含 101 个动作类别、13,320 个视频片段，总时长约 27 小时。视频均来自 YouTube 的真实用户上传内容，包含相机运动、杂乱背景、光照变化、部分遮挡和低质量帧等挑战因素。视频分辨率为 320×240，帧率为 25 fps，平均时长 7.21 秒。')
add_body('101 个动作类别按语义分为五大类型：体育运动（50 类）、仅身体运动（16 类）、人与物交互（20 类）、演奏乐器（10 类）、人与人交互（5 类）。数据集按 25 个组组织，同一组内的视频共享相似背景或演员，官方提供 3 个训练/测试划分（split），确保同一组的视频不会同时出现在训练集和测试集中，避免数据泄露。')
add_body('本课题将使用官方提供的全部 3 个 split 进行实验，报告 3 个 split 的平均准确率。每个 split 的训练集约 9,537 个视频，测试集约 3,783 个视频。')

# ========== 七、实验分析 ==========
add_title('七、实验分析', level=1)

add_title('7.1 评价指标', level=2)
add_body('本课题采用以下评价指标：')
add_body('top-1 准确率：模型预测的最高概率类别与真实类别一致的样本比例，是核心评价指标。')
add_body('top-5 准确率：模型预测的前 5 个最高概率类别中包含真实类别的样本比例，作为辅助评价指标。')
add_body('显存峰值：训练过程中 GPU 显存的最大占用量，必须不超过 2 GB。')
add_body('吞吐量：单位时间内处理的视频帧数或视频数，反映模型的训练与推理效率。')

add_title('7.2 实验设计', level=2)
add_body('主实验：在 2 GB 显存约束下，对比朴素 3D-CNN 基线、2D+时序聚合路线、轻量 3D 路线的 top-1/top-5 准确率，验证相对基线提升不少于 4 个百分点的目标。')
add_body('采样策略消融实验：对最优路线，在均匀/稠密/自适应三种采样策略、8/16/32 帧三种帧数下进行网格实验，分析采样策略对准确率的影响。')
add_body('显存优化消融实验：逐项开关混合精度训练、梯度检查点等优化技术，量化每项技术对显存峰值、训练速度与准确率的影响。')
add_body('时空投入对比实验：固定 2 GB 显存，对比时间优先、空间优先、均衡三种配置的准确率，回答时空建模优先级的核心问题。')
add_body('错误归因分析：生成混淆矩阵，按五大动作类型分组计算准确率，对比两条路线的错误模式，选取典型案例进行 Grad-CAM 可视化分析。')

add_title('7.3 实验设置', level=2)
add_body('所有核心实验均设置不少于 3 个随机种子，报告均值与标准差。采用配对 t 检验验证性能提升的统计显著性，显著性水平设为 0.05。')
add_body('训练框架采用 PyTorch，视频读取采用 Decord 或 ffmpeg 抽帧，光流提取采用 TV-L1 算法。优化器采用 SGD（动量 0.9，权重衰减 1e-4），学习率调度采用余弦退火策略。数据增强包括随机裁剪、水平翻转、颜色抖动、尺度抖动等。')
add_body('按采样策略分组报告结果，即对每种采样策略单独统计准确率，以便分析不同策略的性能差异。')

# ========== 八、结论 ==========
add_title('八、结论', level=1)
add_body('本课题预期得出以下结论：')
add_body('第一，在 2 GB 极低显存预算下，2D 骨干网络结合强时序聚合的路线预期优于朴素 3D 卷积路线。原因在于 3D 卷积的中间激活值显存开销大，在 2 GB 约束下只能使用极小的模型、极少的帧数和极低的分辨率，反而不如 2D 卷积配合高效时序聚合的方案。预期相对朴素 3D-CNN 基线可实现不少于 4 个百分点的 top-1 准确率提升。')
add_body('第二，帧采样策略对准确率有显著影响。均匀采样在长视频上表现稳定，稠密采样在短期精细动作上有优势，自适应采样有望在相同帧数预算下获得更优的信息量，但实现复杂度较高。在低显存约束下，均匀采样配合适当的帧数预期是综合最优的选择。')
add_body('第三，关于低显存预算下时空建模优先级的实证结论：对于运动密集型动作（如体育运动类），时间维度的投入回报更高，应优先保证足够的输入帧数；对于外观依赖型动作（如人与物交互类），空间维度更重要，应优先保证较高的输入分辨率。整体而言，在 2 GB 显存预算下，空间特征是基础，时间建模在此基础上提供增量提升，因此建议采用“保空间分辨率、用轻量时序聚合”的资源分配策略。')
add_body('第四，混合精度训练与梯度检查点等显存优化技术可在几乎不损失准确率的前提下显著降低显存占用，是低显存训练的必要手段。其中混合精度训练可降低约 40% 显存，梯度检查点可进一步降低中间激活值的显存开销。')
add_body('第五，本课题建立的可复现实验框架与系统消融分析结果，可为低资源视频动作识别领域的后续研究提供有价值的参考基准与方法论指导。')

# ========== 九、参考文献 ==========
add_title('九、参考文献', level=1)

refs = [
    '[1] Wang L, Xiong Y, Wang Z, et al. Temporal segment networks: Towards good practices for deep action recognition[C]//European Conference on Computer Vision (ECCV). 2016: 20-36.',
    '[2] Carreira J, Zisserman A. Quo vadis, action recognition? A new model and the kinetics dataset[C]//IEEE Conference on Computer Vision and Pattern Recognition (CVPR). 2017: 6299-6308.',
    '[3] Soomro K, Zamir A R, Shah M. UCF101: A Dataset of 101 Human Action Classes from Videos in the Wild[R]. CRCV-TR-12-01, University of Central Florida, 2012.',
    '[4] Tran D, Wang H, Torresani L, et al. A closer look at spatiotemporal convolutions for action recognition[C]//CVPR. 2018: 6450-6459.',
    '[5] Feichtenhofer C, Fan H, Malik J, et al. SlowFast networks for video recognition[C]//ICCV. 2019: 6202-6211.',
    '[6] Lin J, Gan C, Han S. TSM: Temporal shift module for efficient video understanding[C]//ICCV. 2019: 7083-7093.',
    '[7] Girdhar R, Carreira J, Doersch C, et al. Video action transformer network[C]//CVPR. 2019: 244-253.',
    '[8] Qiu Z, Yao T, Mei T. Learning spatio-temporal representation with pseudo-3D residual networks[C]//ICCV. 2017: 5534-5542.',
    '[9] Hara K, Kataoka H, Satoh Y. Can spatiotemporal 3D CNNs retrace the history of 2D CNNs and ImageNet?[C]//CVPR. 2018: 6546-6555.',
    '[10] Micikevicius P, Narang S, Alben J, et al. Mixed precision training[C]//International Conference on Learning Representations (ICLR). 2018.',
    '[11] Chen T, Xu B, Zhang C, et al. Training deep nets with sublinear memory cost[J]. arXiv preprint arXiv:1604.06174, 2016.',
    '[12] Selvaraju R R, Cogswell M, Das A, et al. Grad-CAM: Visual explanations from deep networks via gradient-based localization[C]//ICCV. 2017: 618-626.',
    '[13] Kuehne H, Jhuang H, Garrote E, et al. HMDB: a large video database for human motion recognition[C]//ICCV. 2011: 2556-2563.',
    '[14] Kay W, Carreira J, Simonyan K, et al. The kinetics human action video dataset[J]. arXiv preprint arXiv:1705.06950, 2017.',
    '[15] Wang L, Qiao Y, Tang X. Action recognition with trajectory-pooled deep-convolutional descriptors[C]//CVPR. 2015: 4305-4314.',
]

for ref in refs:
    p = doc.add_paragraph(ref)
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.left_indent = Pt(24)
    p.paragraph_format.hanging_indent = Pt(24)
    for run in p.runs:
        run.font.name = '宋体'
        run.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
        run.font.size = Pt(11)

# 保存
output_path = r'C:\Users\Administrator\Desktop\A11题\A11开题报告_资源约束下的视频动作识别时空解耦建模研究.docx'
doc.save(output_path)
print(f'开题报告已生成: {output_path}')

# 统计字数
total_chars = 0
for para in doc.paragraphs:
    total_chars += len(para.text)
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            total_chars += len(cell.text)
print(f'总字符数（含表格）: {total_chars}')
