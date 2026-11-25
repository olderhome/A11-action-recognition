# -*- coding: utf-8 -*-
"""生成课题A11相关研究调研报告 Word 文档"""
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

doc = Document()

style = doc.styles['Normal']
style.font.name = '宋体'
style.font.size = Pt(12)
style.element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
style.paragraph_format.line_spacing = 1.5
style.paragraph_format.first_line_indent = Pt(24)

for section in doc.sections:
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)

def add_title(text, level=0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 0 else WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.first_line_indent = Pt(0)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run(text)
    run.font.name = '黑体'
    run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
    if level == 0:
        run.font.size = Pt(18); run.bold = True
    elif level == 1:
        run.font.size = Pt(15); run.bold = True
    elif level == 2:
        run.font.size = Pt(13); run.bold = True
    return p

def add_body(text):
    return doc.add_paragraph(text)

def add_table(headers, rows):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
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
        run.font.size = Pt(10)
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
            run.font.size = Pt(10)
    doc.add_paragraph()
    return table

# ========== 标题 ==========
add_title('课题A11相关研究调研报告', level=0)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.first_line_indent = Pt(0)
run = p.add_run('资源约束下的视频动作识别时空解耦建模研究')
run.font.name = '黑体'
run.element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
run.font.size = Pt(14); run.bold = True
doc.add_paragraph()

# ========== 一、引言 ==========
add_title('一、引言', level=1)
add_body('视频动作识别是计算机视觉领域的核心研究方向之一，旨在从视频序列中自动识别人类行为类别。近年来，随着深度学习技术的发展，视频动作识别取得了显著进展，但模型的计算量与显存需求也随之急剧增长。在边缘设备、移动端以及资源受限的计算环境中，如何在极低显存预算下保持较高的识别准确率，成为学术界与工业界共同关注的问题。')
add_body('本课题（A11）聚焦于资源约束下的视频动作识别时空解耦建模研究，要求在不超过2 GB显存预算下，于UCF101数据集上训练动作识别模型，使top-1准确率相对同预算朴素3D-CNN基线提升不少于4个百分点，并系统研究帧采样策略的影响，最终给出低显存预算下时空建模优先级的实证结论。')
add_body('为明确本课题的研究定位与创新空间，本报告从视频动作识别模型架构、帧采样策略、显存优化技术、开源框架四个维度，系统梳理当前国内外相关研究现状，分析已有工作的优势与不足，为本课题的技术路线选择提供依据。')

# ========== 二、视频动作识别模型架构研究现状 ==========
add_title('二、视频动作识别模型架构研究现状', level=1)

add_title('2.1 3D卷积神经网络路线', level=2)
add_body('3D卷积神经网络通过在空间维度之外引入时间维度的卷积核，直接对视频的时空特征进行联合建模。该路线的代表性工作包括：')
add_body('C3D（Tran等，2015）是首个大规模应用的3D CNN架构，采用简单的3×3×3卷积核和池化核，在Sports-1M数据集上预训练后迁移到UCF101和HMDB51。C3D的参数量约为78.4M，在UCF101上达到83.08%的top-1准确率，但其计算量大、显存需求高，且无法利用ImageNet预训练权重。')
add_body('I3D（Carreira和Zisserman，CVPR 2017）提出将成熟的2D ImageNet架构（如Inception-v1）“膨胀”为3D架构，通过在时间维度重复2D滤波器权重并归一化，实现了ImageNet预训练到3D模型的迁移。I3D在Kinetics数据集预训练后，在UCF101上达到98.0%、HMDB51上达到80.9%的准确率，大幅刷新了当时的纪录。但I3D的参数量约为25M，训练需要大量GPU资源（原论文使用32张K40 GPU），在低显存环境下难以直接应用。')
add_body('R(2+1)D（Tran等，CVPR 2018）将3D卷积分解为空间2D卷积与时间1D卷积的串联，这种分解不仅增加了非线性变换的次数，还使优化更加容易。R(2+1)D在保持与3D卷积相近表达能力的同时，降低了计算复杂度。')
add_body('X3D（Feichtenhofer，CVPR 2020）受 EfficientNet 的网络扩展思想启发，从一个轻量级的2D网络（X2D）出发，通过联合扩展网络宽度、深度、时间分辨率和空间分辨率，搜索出一系列高效的3D CNN架构（X3D-XS/S/M/L）。X3D-XS仅需约4M参数和2.1G FLOPs，在Kinetics-400上达到73.1%的准确率，是目前效率最高的3D CNN之一。X3D采用深度可分离3D卷积和通道注意力，显著降低了显存占用。')
add_body('SlowFast（Feichtenhofer等，ICCV 2019）提出快慢双路径架构：慢路径以低帧率处理视频，捕捉空间语义信息；快路径以高帧率处理视频，捕捉运动信息。两条路径通过侧向连接融合特征。SlowFast在Kinetics-400上达到79.8%的准确率，但其双路径设计增加了显存开销。')

add_title('2.2 2D骨干网络与时序聚合路线', level=2)
add_body('该路线采用2D卷积神经网络提取单帧空间特征，再通过轻量级的时序聚合模块对多帧特征进行融合，避免了3D卷积的高显存开销。')
add_body('TSN（Wang等，ECCV 2016）提出时序分段网络，将视频均匀划分为K个片段，每个片段随机采样一帧，通过2D CNN提取特征后，采用分段共识函数（平均池化）进行时序聚合。TSN的稀疏采样策略大幅降低了计算量，同时覆盖了视频的全局时序结构。在UCF101上，TSN（BN-Inception骨干）达到93.5%的准确率。TSN还系统探索了跨模态预训练、部分Batch Normalization、角点裁剪等训练技巧，成为后续视频动作识别的标准配置。')
add_body('TSM（Lin等，ICCV 2019）提出时序移位模块，通过在时间维度上移位部分特征通道，实现零额外参数、零额外计算量的帧间信息交互。TSM可以即插即用地集成到任意2D CNN中，在保持2D卷积推理速度的同时，显著提升时序建模能力。在UCF101上，TSM（ResNet50骨干，Kinetics-400预训练）达到94.50%的top-1准确率。TSM的显存占用与2D CNN基本相同，是低显存环境下的理想选择。')
add_body('TEA（Chen等，ACM MM 2020）提出时序激励与聚合模块，通过多步时序激励捕捉短期运动特征，再通过时序聚合模块进行长程时序建模。TEA在Something-Something V1上达到了当时的最佳性能。')
add_body('GSM（Luo等，CVPR 2022）提出门控时空建模模块，通过门控机制自适应地融合空间特征与时序特征，进一步提升了2D骨干路线的时序建模能力。')

add_title('2.3 移动端与边缘端高效视频模型', level=2)
add_body('随着视频理解在移动设备和边缘端的应用需求增长，专门针对资源受限环境设计的高效视频模型成为研究热点。')
add_body('MoViNets（Kondratyuk等，CVPR 2021）由Google Research提出，是一系列面向移动端的高效视频网络。MoViNets采用神经架构搜索（NAS）设计高效的3D CNN构建块，并通过因果卷积支持流式视频推理。其核心创新包括：流式缓冲器（stream buffer）减少峰值内存使用、因果深度可分离卷积、以及网络架构搜索。MoViNets-A0仅需约3.1M参数，可在智能手机上实时运行。在Kinetics-600上，MoViNets-A5达到78.4%的准确率，同时推理速度优于同量级的X3D模型。')
add_body('SqueezeTime（2024）提出将视频的时间维度压缩到通道维度，设计了通道-时间学习（CTL）模块来捕捉时序动态。SqueezeTime在移动视频理解任务上超越了E3d-XS等方法，同时测试时间减少约20%。')
add_body('Resource-Efficient RGB-Only Action Recognition for Edge Deployment（2026）针对边缘部署场景，在X3D风格骨干上集成TSM时序建模，并引入3D通用倒置瓶颈（Ghost逐点卷积）、选择性时序适配和轻量级无参数注意力，在极低资源预算下实现了具有竞争力的准确率。')
add_body('CoDAT（2026）提出协作双注意力Transformer，结合低成本时序建模，用于高效边缘动作识别。该工作指出3D CNN计算量大、显存需求高，不适合边缘部署，而TSM等零参数时序建模方法是边缘端的可行选择。')

add_title('2.4 Transformer与状态空间模型在视频理解中的应用', level=2)
add_body('近年来，Transformer架构和状态空间模型（SSM）也被引入视频理解领域，为高效时序建模提供了新的思路。')
add_body('Video Swin Transformer（Liu等，ICCV 2022）将Swin Transformer扩展到3D，通过3D窗口多头自注意力进行时空建模，在Kinetics-400上达到82.3%的准确率。但Transformer架构的显存需求通常高于CNN，在低显存环境下应用受限。')
add_body('VideoMamba（Tong等，ECCV 2024）由中科院深圳先进院提出，是首个仅基于状态空间模型（Mamba）的高效视频理解架构。VideoMamba利用Mamba的线性计算复杂度和长序列建模能力，在视频理解任务上展现出视觉领域可扩展性、短期动作敏感性、长视频优势和多模态兼容性等特性。在相同计算量下，VideoMamba的性能优于Video Swin Transformer，且推理速度更快。')
add_body('Temporal Shift Vision Transformer Adapter（2024）提出TSM-Adapter，将时序移位思想与ViT适配器结合，仅训练16.5%的新参数即可实现12.87%的准确率提升，为高效微调大型预训练ViT提供了新思路。')

add_title('2.5 模型架构对比总结', level=2)
add_table(
    ['模型', '路线', '参数量', 'UCF101 top-1', '显存需求', '核心特点'],
    [
        ['C3D', '3D CNN', '78.4M', '83.1%', '高', '首个大规模3D CNN'],
        ['I3D', '3D CNN', '25M', '98.0%*', '极高', '2D膨胀3D，Kinetics预训练'],
        ['R(2+1)D', '3D CNN', '~30M', '~94%*', '高', '2D+1D分解卷积'],
        ['X3D-XS', '3D CNN', '~4M', '~90%*', '中', '网络扩展搜索，高效3D'],
        ['SlowFast', '3D CNN', '~34M', '~95%*', '高', '快慢双路径'],
        ['TSN', '2D+时序', '~12M', '93.5%', '低', '稀疏分段采样，平均池化'],
        ['TSM', '2D+时序', '~24M', '94.5%*', '低', '零参数时序移位'],
        ['MoViNet-A0', '高效3D', '~3.1M', '~85%*', '极低', 'NAS搜索，流式推理'],
        ['VideoMamba', 'SSM', '~25M', '~93%*', '中', '线性复杂度，长序列建模'],
    ]
)
add_body('注：标*的结果使用了Kinetics-400或更大规模数据集预训练，未标注的为ImageNet预训练或从头训练。不同实验设置（帧数、分辨率、测试协议）存在差异，数值仅供参考。')

# ========== 三、帧采样策略研究现状 ==========
add_title('三、帧采样策略研究现状', level=1)
add_body('帧采样策略决定了从视频中选取哪些帧输入模型，直接影响模型的计算量、显存占用和识别准确率。当前帧采样策略主要分为以下几类：')

add_title('3.1 均匀采样', level=2)
add_body('均匀采样是最经典的帧采样策略，将视频沿时间维度均匀划分为K个片段，每个片段等间隔或随机选取一帧。TSN是均匀采样的代表性工作，其分段采样策略保证了对视频全局时序结构的覆盖，同时计算量仅为稠密采样的1/K。')
add_body('均匀采样的优势在于实现简单、计算量可控、对长视频有较好的全局覆盖。其局限性在于无法根据视频内容自适应调整采样位置，可能在运动剧烈的时间段采样不足，而在静止时间段采样冗余。')

add_title('3.2 稠密采样', level=2)
add_body('稠密采样从视频中连续选取N帧（通常为8帧、16帧或32帧），是3D CNN（如C3D、I3D、X3D）的标准输入方式。稠密采样能够捕捉精细的短期运动模式，适合需要精细运动分析的动作类别。')
add_body('稠密采样的局限性在于：第一，连续帧之间存在高度冗余，浪费计算资源；第二，对于长视频，稠密采样只能覆盖视频的一小段，可能遗漏关键动作阶段；第三，帧数增加会线性增加3D卷积的显存占用，在低显存环境下受到严格限制。')

add_title('3.3 自适应采样', level=2)
add_body('自适应采样根据视频内容动态选择帧，旨在在相同帧数预算下选取信息量最大的帧。近年来，自适应采样在长视频理解和高效视频识别中受到广泛关注。')
add_body('基于运动强度的自适应采样通过计算帧间像素差异或光流幅度评估运动强度，在运动剧烈的时间段多采样、在静止时间段少采样。这类方法实现简单，但运动强度高的帧不一定包含最具判别性的信息。')
add_body('基于学习的自适应采样使用可训练的策略网络或评分函数来评估每帧的重要性，动态选择关键帧。TAPS（ACCV 2024）提出基于时序注意力的剪枝与缩放方法，使用轻量级策略网络对每个滤波器的重要性进行逐层决策，保留重要滤波器、缩放过时跳过不重要的滤波器，实现了动态计算分配。Uni-AdaFocus（2024）提出统一的时空动态计算框架，将动态帧采样与空间动态计算相结合，自适应地选择信息量最大的帧和图像区域。')
add_body('在长视频理解领域，FOCUS（2026）提出高效关键帧选择方法，采用两阶段探索-利用策略，仅处理不到2%的帧即可在长视频基准上取得一致提升。AdaRD-Key（2025）提出自适应相关性-多样性关键帧采样，通过最大化相关性-多样性目标函数选择信息丰富且非冗余的帧。VideoBrain（2026）提出学习自适应帧采样的智能体框架，包含均匀采样智能体、CLIP检索智能体等多种采样策略。')
add_body('然而，当前自适应采样研究多集中于长视频问答和视频大语言模型领域，针对低显存约束下短视频动作识别的自适应采样研究仍相对不足，这也是本课题的研究空间之一。')

add_title('3.4 帧采样策略对比', level=2)
add_table(
    ['采样策略', '代表工作', '计算量', '全局覆盖', '内容适应性', '实现复杂度'],
    [
        ['均匀采样', 'TSN', '低', '好', '无', '低'],
        ['稠密采样', 'C3D, I3D', '高', '差（仅局部）', '无', '低'],
        ['运动自适应', '传统方法', '中', '中', '有（运动）', '中'],
        ['学习自适应', 'TAPS, AdaFocus', '中', '好', '有（任务相关）', '高'],
        ['关键帧选择', 'FOCUS, AdaRD', '极低', '好', '有（语义）', '高'],
    ]
)

# ========== 四、显存优化与低资源训练技术 ==========
add_title('四、显存优化与低资源训练技术', level=1)
add_body('在低显存预算下训练深度视频模型，需要综合运用多种显存优化技术。当前主流的显存优化技术包括以下几类：')

add_title('4.1 混合精度训练', level=2)
add_body('混合精度训练（Mixed Precision Training，AMP）使用FP16（半精度）进行前向计算和梯度存储，同时保留FP32（单精度）的主权重和优化器状态，以保证数值稳定性。FP16的显存占用仅为FP32的一半，因此混合精度训练通常可节省30%-50%的GPU显存。')
add_body('PyTorch提供了torch.cuda.amp模块，通过autocast上下文管理器和GradScaler实现混合精度训练。在视频动作识别中，混合精度训练是降低显存占用的首选技术，且几乎不损失准确率。对于Batch Normalization等对数值精度敏感的层，通常保持FP32计算以保证稳定性。')

add_title('4.2 梯度检查点（激活检查点）', level=2)
add_body('梯度检查点（Gradient Checkpointing），又称激活检查点（Activation Checkpointing）或激活重计算（Activation Recomputation），是一种以计算时间换取显存空间的技术。在标准训练中，前向传播的所有中间激活值都需要保存以供反向传播计算梯度，这些激活值往往占据了显存的大部分（尤其是3D CNN和深层网络）。梯度检查点在前向传播时只保存部分层的激活值，反向传播时重新计算未保存的激活值，从而大幅降低显存占用。')
add_body('研究表明，梯度检查点可将激活值显存降低2-3倍，代价是训练时间增加约20%-30%。PyTorch提供了torch.utils.checkpoint模块，可方便地对任意模块应用梯度检查点。在视频动作识别中，梯度检查点是在低显存下训练深层3D CNN的关键技术。')
add_body('极端形式的激活重计算（Activation Recomputation）在前向传播时不保存任何中间激活值，反向传播时全部重新计算，可将激活显存降至接近零，但训练时间约增加一倍，仅在显存极度紧张时使用。')

add_title('4.3 梯度累积', level=2)
add_body('梯度累积（Gradient Accumulation）通过在多个小批量（mini-batch）上累积梯度，然后一次性更新参数，模拟大批量训练的效果。在显存受限的情况下，可以使用较小的批量大小（如batch_size=1或2），通过梯度累积达到等效的大批量大小（如batch_size=16或32），保证训练的稳定性和收敛性。梯度累积不直接减少单步显存，但允许在小批量下稳定训练。')

add_title('4.4 输入分辨率与帧数优化', level=2)
add_body('视频模型的显存占用与输入分辨率和帧数密切相关。3D卷积的激活值显存与帧数×高度×宽度成正比，因此降低输入分辨率和帧数是最直接的显存优化手段。')
add_body('在空间维度，常用的分辨率包括224×224、160×160、112×112等。降低分辨率可显著减少显存，但可能损失细节信息。在时间维度，常用的帧数包括8帧、16帧、32帧等。帧数增加可提升时序建模能力，但线性增加3D卷积的显存占用。')
add_body('X3D等工作通过系统的网络扩展实验，研究了分辨率、帧数、通道数、深度等维度之间的最优权衡，为低显存配置提供了参考。')

add_title('4.5 模型轻量化技术', level=2)
add_body('除上述训练优化技术外，模型架构层面的轻量化设计也是降低显存的重要手段：')
add_body('深度可分离卷积（Depthwise Separable Convolution）将标准卷积分解为深度卷积和逐点卷积，大幅减少参数量和计算量。X3D、MobileNet等高效架构均采用此技术。')
add_body('通道数缩减通过减少网络各层的通道数来降低参数量和激活值显存。小模型（如ResNet-18而非ResNet-50）是低显存环境的自然选择。')
add_body('知识蒸馏（Knowledge Distillation）通过大模型（教师）指导小模型（学生）训练，使小模型在保持较低参数量的同时获得较高准确率，是模型压缩的常用技术。')

add_title('4.6 显存优化技术效果总结', level=2)
add_table(
    ['优化技术', '显存节省', '训练时间影响', '准确率影响', '适用场景'],
    [
        ['混合精度训练', '30%-50%', '几乎无影响', '几乎无损失', '所有场景，首选'],
        ['梯度检查点', '激活显存降2-3倍', '增加20%-30%', '几乎无损失', '深层网络、3D CNN'],
        ['梯度累积', '间接（允许小batch）', '略有增加', '几乎无损失', '需要稳定训练时'],
        ['降低分辨率', '显著', '减少', '可能损失', '显存极度紧张时'],
        ['减少帧数', '显著（3D CNN）', '减少', '可能损失', '显存极度紧张时'],
        ['模型轻量化', '显著', '减少', '可能损失', '边缘部署'],
    ]
)

# ========== 五、开源框架与工具 ==========
add_title('五、开源框架与工具', level=1)

add_title('5.1 MMAction2', level=2)
add_body('MMAction2是由商汤科技和香港中文大学联合开发的视频理解开源框架，基于PyTorch和MMCV构建，是目前最全面、最活跃的视频动作识别开源框架之一。')
add_body('MMAction2支持丰富的模型架构，包括TSN、TSM、I3D、C3D、R(2+1)D、X3D、SlowFast、CSN、TimeSformer、Video Swin Transformer等。框架内置了UCF101、HMDB51、Kinetics-400/600/700、Something-Something V1/V2等主流数据集的数据加载和预处理流程，并提供了大量预训练模型权重和基准结果。')
add_body('在UCF101数据集上，MMAction2提供了详细的模型基准。例如，TSN（ResNet50骨干，ImageNet预训练）达到83.03%的top-1准确率，GPU显存占用约8332MB；TSM（ResNet50骨干，Kinetics-400预训练）达到94.50%的top-1准确率，GPU显存占用约10389MB。这些基准结果为本课题的基线复现提供了重要参考。')
add_body('MMAction2支持混合精度训练、梯度检查点等显存优化技术，且配置文件系统灵活，便于进行消融实验。框架提供了完善的训练、测试、可视化工具链，是本课题的首选开发框架。')

add_title('5.2 PyTorchVideo', level=2)
add_body('PyTorchVideo是由Facebook AI Research（FAIR）开发的视频理解深度学习库，基于PyTorch构建。PyTorchVideo提供了丰富的视频模型实现（包括SlowFast、X3D、I3D等）、数据加载器、视频解码器和预训练模型。其特点是与PyTorch生态深度集成，API设计简洁，适合研究原型开发。')

add_title('5.3 TensorFlow Model Garden与MoViNets', level=2)
add_body('Google的TensorFlow Model Garden提供了MoViNets等高效视频模型的官方实现和预训练权重。MoViNets支持TensorFlow Lite部署，可在移动设备上实时运行。对于需要在移动端或边缘端部署的场景，MoViNets是重要的参考实现。')

add_title('5.4 其他工具', level=2)
add_body('视频读取与处理方面，Decord是高效的视频读取库，支持随机帧访问和批量解码，比OpenCV的VideoCapture快数倍。ffmpeg是视频处理的标准工具，可用于视频抽帧、转码、分辨率调整等。光流提取方面，TV-L1算法是最常用的稠密光流提取方法，OpenCV提供了GPU加速实现。')
add_body('实验管理方面，Weights & Biases（WandB）和TensorBoard是常用的实验跟踪与可视化工具，可记录训练曲线、显存使用、超参数等信息，便于实验对比和复现。')

# ========== 六、研究空白与本课题定位 ==========
add_title('六、研究空白与本课题定位', level=1)

add_title('6.1 当前研究存在的不足', level=2)
add_body('通过对相关研究的系统梳理，可以发现当前研究在以下方面存在不足：')
add_body('第一，极低显存预算（≤2 GB）下的视频动作识别研究不足。现有高效视频模型（如X3D、MoViNets）虽然参数量和计算量较低，但其训练过程通常仍需要较大显存（如batch_size=8或16、多GPU训练），针对单卡≤2 GB显存预算下的系统研究较少。现有工作多关注推理效率（FLOPs、参数量、推理速度），而对训练阶段的显存峰值关注不足。')
add_body('第二，2D+时序聚合路线与轻量3D路线在相同极低显存预算下的公平对比研究不足。现有研究通常在各自的最优配置下报告结果，缺乏在严格相同显存约束下两条路线的系统性对比。不同论文的实验设置（帧数、分辨率、批量大小、预训练数据集）差异较大，难以直接比较。')
add_body('第三，帧采样策略在低显存约束下的系统消融研究不足。现有帧采样策略研究多集中于长视频理解和视频大语言模型领域，针对短视频动作识别、尤其是在低显存约束下不同采样策略（均匀/稠密/自适应）的性能对比和适用场景分析尚不充分。')
add_body('第四，低显存预算下时空建模优先级的实证结论缺失。现有工作分别研究了空间建模和时间建模的改进，但缺乏在固定显存预算下，系统比较“将资源投入时间维”与“将资源投入空间维”哪种回报更高的实证研究。这一问题对于低资源视频模型的架构设计具有重要指导意义。')
add_body('第五，显存优化技术对视频模型准确率影响的定量消融研究不足。混合精度训练、梯度检查点等技术被广泛使用，但其在视频动作识别任务上对准确率、训练速度、显存峰值的定量影响，以及不同技术之间的组合效果，尚缺乏系统的消融分析。')

add_title('6.2 本课题的研究定位与创新点', level=2)
add_body('针对上述研究空白，本课题定位为：在≤2 GB极低显存预算约束下，系统研究视频动作识别的时空解耦建模方法，通过两条技术路线对照、帧采样策略消融、显存优化技术分析和错误归因，给出低显存预算下时空建模优先级的实证结论。')
add_body('本课题的创新点主要体现在以下方面：')
add_body('第一，严格的极低显存预算约束。本课题将显存峰值≤2 GB作为硬约束，所有模型和实验均在此约束下进行配置和比较，研究结论对边缘设备和低资源场景具有直接的参考价值。')
add_body('第二，两条路线的公平对照。在完全相同的显存预算下，系统对比2D骨干+时序聚合路线与轻量3D卷积路线的性能差异，控制变量包括输入帧数、空间分辨率、训练轮数、优化器等，确保对比的公平性。')
add_body('第三，帧采样策略的系统消融。在相同显存预算下，对均匀采样、稠密采样、自适应采样三种策略进行网格实验，分析采样策略与模型架构、动作类型之间的匹配关系。')
add_body('第四，时空建模优先级的实证结论。通过固定显存预算下的资源分配对比实验（时间优先vs空间优先vs均衡），定量回答“低显存预算下时间维和空间维哪个更值得投入”的核心科学问题。')
add_body('第五，完整的可复现实验框架。建立包含数据构造、模型训练、显存监控、消融实验、错误归因的完整实验流程，所有核心实验提供不少于3个随机种子的完整结果，确保结论的可靠性和可复现性。')

# ========== 七、参考文献 ==========
add_title('七、参考文献', level=1)

refs = [
    '[1] Wang L, Xiong Y, Wang Z, et al. Temporal segment networks: Towards good practices for deep action recognition[C]//ECCV. 2016: 20-36.',
    '[2] Carreira J, Zisserman A. Quo vadis, action recognition? A new model and the kinetics dataset[C]//CVPR. 2017: 6299-6308.',
    '[3] Soomro K, Zamir A R, Shah M. UCF101: A Dataset of 101 Human Action Classes from Videos in the Wild[R]. CRCV-TR-12-01, 2012.',
    '[4] Tran D, Bourdev L, Fergus R, et al. Learning spatiotemporal features with 3D convolutional networks[C]//ICCV. 2015: 4489-4497.',
    '[5] Tran D, Wang H, Torresani L, et al. A closer look at spatiotemporal convolutions for action recognition[C]//CVPR. 2018: 6450-6459.',
    '[6] Feichtenhofer C. X3D: Expanding architectures for efficient video recognition[C]//CVPR. 2020: 203-213.',
    '[7] Feichtenhofer C, Fan H, Malik J, et al. SlowFast networks for video recognition[C]//ICCV. 2019: 6202-6211.',
    '[8] Lin J, Gan C, Han S. TSM: Temporal shift module for efficient video understanding[C]//ICCV. 2019: 7083-7093.',
    '[9] Chen Y, Kalantidis Y, Li J, et al. TEA: Temporal excitation and aggregation for action recognition[C]//ACM MM. 2020: 903-911.',
    '[10] Kondratyuk D, Yuan L, Li Y, et al. MoViNets: Mobile video networks for efficient video recognition[C]//CVPR. 2021: 16015-16025.',
    '[11] Liu Z, Ning J, Cao Y, et al. Video Swin Transformer[C]//ICCV. 2022: 3225-3234.',
    '[12] Tong Z, Song Y, Wang J, et al. VideoMamba: State space model for efficient video understanding[C]//ECCV. 2024.',
    '[13] Dinai O, et al. TAPS: Temporal attention-based pruning and scaling for efficient video action recognition[C]//ACCV. 2024.',
    '[14] Li M, et al. Uni-AdaFocus: Spatial-temporal dynamic computation for video recognition[J]. arXiv preprint arXiv:2412.11228, 2024.',
    '[15] Chen T, Xu B, Zhang C, et al. Training deep nets with sublinear memory cost[J]. arXiv preprint arXiv:1604.06174, 2016.',
    '[16] Micikevicius P, Narang S, Alben J, et al. Mixed precision training[C]//ICLR. 2018.',
    '[17] Contributors M. MMAction2: Open mmlab action understanding toolbox and benchmark[J]. arXiv preprint arXiv:2104.10577, 2021.',
    '[18] Hao H, et al. PyTorchVideo: A deep learning library for video understanding[J]. arXiv preprint arXiv:2111.09887, 2021.',
    '[19] Resource-Efficient RGB-Only Action Recognition for Edge Deployment[J]. arXiv preprint arXiv:2602.10818, 2026.',
    '[20] CoDAT: Collaborative dual-attention transformer with low-cost temporal modeling for efficient edge action recognition[J]. arXiv preprint arXiv:2608.06691, 2026.',
    '[21] No time to waste: Squeeze time into channel for mobile video understanding[J]. arXiv preprint arXiv:2405.08344, 2024.',
    '[22] A survey on backbones for deep video action recognition[J]. arXiv preprint arXiv:2405.05584, 2024.',
    '[23] SMART-Vision: Survey of modern action recognition techniques in vision[J]. arXiv preprint arXiv:2501.13066, 2025.',
    '[24] FOCUS: Efficient keyframe selection for long video understanding[C]//OpenReview. 2026.',
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

output_path = r'C:\Users\Administrator\Desktop\A11题\A11相关研究调研报告.docx'
doc.save(output_path)
print(f'调研报告已生成: {output_path}')

total_chars = 0
for para in doc.paragraphs:
    total_chars += len(para.text)
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            total_chars += len(cell.text)
print(f'总字符数（含表格）: {total_chars}')
