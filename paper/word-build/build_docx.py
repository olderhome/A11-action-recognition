from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


BUILD_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = BUILD_ROOT.parents[1]
OUTPUT = BUILD_ROOT / "A11_技术论文_draft.docx"
EQUATIONS = BUILD_ROOT / "equations"

FONT = "Microsoft YaHei"
BLACK = RGBColor(0, 0, 0)
DARK = "14213D"
TEAL = "1B7F79"
ORANGE = "C66A31"
PALE = "F5F7F7"
LINE = "D9D9D9"


def read_json(relative: str):
    return json.loads((PROJECT_ROOT / relative).read_text(encoding="utf-8"))


SUMMARY = read_json(
    "results/feature_pipeline/main_20261125_193324/summary/summary.json")
MEMORY = read_json(
    "results/memory/memory_20261125_210742/matrix.json")
DATA = read_json("results/data/ucf101_dataset_validation.json")
SPLIT = read_json("results/data/ucf101_split1_summary.json")
ERROR = read_json(
    "results/feature_pipeline/main_20261125_193324/"
    "error_analysis/r2plus1d18/error_summary.json")

AGG = {
    (row["suite"], row["config"], row["probe_type"]): row
    for row in SUMMARY["aggregate"]
}
COMP = {
    (row["candidate"], row["candidate_probe"]): row
    for row in SUMMARY["comparisons"]
}
MEM = {row["name"]: row for row in MEMORY}


def pct(value: float, digits: int = 2) -> str:
    return f"{value * 100:.{digits}f}%"


def pm(row: dict, field: str, digits: int = 2) -> str:
    return (
        f"{row[field + '_mean'] * 100:.{digits}f}±"
        f"{row[field + '_std'] * 100:.{digits}f}%"
    )


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=90, start=90, bottom=90, end=90):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (
            ("top", top), ("start", start),
            ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), LINE)


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    header = OxmlElement("w:tblHeader")
    header.set(qn("w:val"), "true")
    tr_pr.append(header)


def set_table_geometry(table, widths):
    total_twips = int(sum(widths) * 1440)
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.first_child_found_in("w:tblW")
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:type"), "dxa")
    tbl_w.set(qn("w:w"), str(total_twips))
    tbl_ind = tbl_pr.first_child_found_in("w:tblInd")
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:type"), "dxa")
    tbl_ind.set(qn("w:w"), "90")
    for column, width in zip(table.columns, widths):
        column.width = Inches(width)


def set_run_font(run, size=10.5, bold=False, color=BLACK):
    run.font.name = FONT
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), FONT)
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), FONT)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), FONT)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color


def add_paragraph(
        document,
        text: str,
        *,
        bold: bool = False,
        style: str | None = None,
        first_line: bool = True,
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
        after: float = 6,
        before: float = 0,
        line: float = 1.3):
    paragraph = document.add_paragraph(style=style)
    paragraph.alignment = align
    paragraph.paragraph_format.space_after = Pt(after)
    paragraph.paragraph_format.space_before = Pt(before)
    paragraph.paragraph_format.line_spacing = line
    if first_line and style is None:
        paragraph.paragraph_format.first_line_indent = Pt(21)
    run = paragraph.add_run(text)
    set_run_font(run, bold=bold)
    return paragraph


def add_bullets(document, items):
    for item in items:
        paragraph = document.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.space_after = Pt(4)
        paragraph.paragraph_format.line_spacing = 1.2
        run = paragraph.add_run(item)
        set_run_font(run, 10.5)


def add_heading(document, text, level=1, page_break=False):
    if page_break:
        document.add_page_break()
    paragraph = document.add_heading(text, level=level)
    paragraph.paragraph_format.keep_with_next = True
    paragraph.paragraph_format.space_before = Pt(14 if level == 1 else 10)
    paragraph.paragraph_format.space_after = Pt(7 if level == 1 else 5)
    for run in paragraph.runs:
        set_run_font(
            run,
            size=16 if level == 1 else 13 if level == 2 else 11,
            bold=True,
            color=BLACK,
        )
    return paragraph


def add_caption(document, text, before=False):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(5 if before else 2)
    paragraph.paragraph_format.space_after = Pt(5 if not before else 8)
    paragraph.paragraph_format.keep_with_next = before
    run = paragraph.add_run(text)
    set_run_font(run, 9, color=RGBColor(70, 75, 80))
    return paragraph


def add_table(document, caption, headers, rows, widths, highlight_row=None):
    add_caption(document, caption, before=True)
    table = document.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    set_table_geometry(table, widths)
    for index, (cell, text, width) in enumerate(
            zip(table.rows[0].cells, headers, widths)):
        cell.width = Inches(width)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_margins(cell)
        set_cell_shading(cell, DARK)
        paragraph = cell.paragraphs[0]
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run(text)
        set_run_font(run, 9.2, bold=True, color=RGBColor(255, 255, 255))
    set_repeat_table_header(table.rows[0])
    for row_index, values in enumerate(rows, start=1):
        cells = table.add_row().cells
        for column_index, (cell, value, width) in enumerate(
                zip(cells, values, widths)):
            cell.width = Inches(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cell)
            fill = "FFFFFF" if row_index % 2 else PALE
            if highlight_row is not None and row_index == highlight_row:
                fill = "DFF0E7"
            set_cell_shading(cell, fill)
            paragraph = cell.paragraphs[0]
            paragraph.alignment = (
                WD_ALIGN_PARAGRAPH.LEFT
                if column_index == 0 else WD_ALIGN_PARAGRAPH.CENTER)
            paragraph.paragraph_format.space_after = Pt(0)
            run = paragraph.add_run(str(value))
            set_run_font(
                run,
                9.5,
                bold=highlight_row is not None and row_index == highlight_row,
            )
    document.add_paragraph().paragraph_format.space_after = Pt(2)


def add_figure(document, relative_path, caption, width_inches=6.1):
    path = PROJECT_ROOT / relative_path
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.keep_with_next = True
    run = paragraph.add_run()
    picture = run.add_picture(str(path), width=Inches(width_inches))
    picture._inline.docPr.set("descr", caption)
    add_caption(document, caption)


def add_equation(document, name, number):
    paragraph = document.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_before = Pt(3)
    paragraph.paragraph_format.space_after = Pt(3)
    run = paragraph.add_run()
    picture = run.add_picture(
        str(EQUATIONS / f"{name}.png"), width=Inches(5.4))
    picture._inline.docPr.set("descr", f"公式 {number}")
    add_caption(document, f"式 ({number})")


def add_page_number(paragraph):
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instruction, separate, text, end])
    set_run_font(run, 9, color=RGBColor(80, 80, 80))


def configure_document(document):
    section = document.sections[0]
    section.top_margin = Inches(0.72)
    section.bottom_margin = Inches(0.68)
    section.left_margin = Inches(0.82)
    section.right_margin = Inches(0.82)
    section.header_distance = Inches(0.28)
    section.footer_distance = Inches(0.28)

    normal = document.styles["Normal"]
    normal.font.name = FONT
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.font.size = Pt(10.5)
    normal.paragraph_format.line_spacing = 1.3
    normal.paragraph_format.space_after = Pt(6)

    for style_name in ("Title", "Heading 1", "Heading 2", "Heading 3"):
        style = document.styles[style_name]
        style.font.name = FONT
        style._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        style.font.color.rgb = BLACK
        style.font.bold = True

    header = section.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = header.add_run("A11 资源约束下的视频动作识别技术研究报告")
    set_run_font(run, 8.5, color=RGBColor(70, 70, 70))
    add_page_number(section.footer.paragraphs[0])


def add_cover(document):
    for _ in range(4):
        document.add_paragraph()
    paragraph = document.add_paragraph(style="Title")
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run("资源约束下的视频动作识别时空解耦建模")
    set_run_font(run, 23, bold=True, color=BLACK)
    paragraph.paragraph_format.space_after = Pt(18)

    subtitle = document.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run("A11 技术研究报告")
    set_run_font(run, 14, color=RGBColor(70, 75, 80))
    subtitle.paragraph_format.space_after = Pt(32)

    for text in (
            "数据集：UCF101 官方 split 1",
            "计算预算：训练显存不超过 2 GiB",
            "作者：Trauma",
            "日期：2026 年 11 月 25 日"):
        paragraph = document.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_after = Pt(8)
        run = paragraph.add_run(text)
        set_run_font(run, 11.5, color=BLACK)
    document.add_page_break()


def add_abstract(document):
    add_heading(document, "摘要", 1)
    add_paragraph(
        document,
        "本文研究 UCF101 上训练显存不超过 2 GiB 的视频动作识别时空建模路线。"
        "数据采用官方 split 1，训练、验证和测试严格按 group 隔离。方法比较 TSN 式"
        "二维骨干时序聚合、朴素 R3D-18 与轻量 R(2+1)D-18，并单独消融均匀、稠密、"
        "运动自适应采样以及等成本时间与空间预算。所有核心头部配置使用 3 个训练种子，"
        "同时记录 CUDA allocated 与 reserved 峰值。"
    )
    add_paragraph(
        document,
        "结果显示，R(2+1)D-18 取得最高 Top-1 83.97%，TSN 时序注意力达到 82.70%，"
        "朴素 R3D-18 为 76.37%。两种候选相对基线分别提升 6.34 和 7.60 个百分点，"
        "达到题目要求。连续稠密采样比均匀分段低 4.10 个百分点。自适应采样准确率接近"
        "均匀采样，但吞吐下降约 68%。等帧像素成本下，空间优先达到 84.19%，时间优先"
        "只有 61.71%。因此，在本文的 2 GiB 冻结主干协议下，应优先投入空间分辨率，"
        "并按应用场景在二维高吞吐路线与轻量三维高精度路线之间选择。"
    )
    paragraph = document.add_paragraph()
    run = paragraph.add_run("关键词：")
    set_run_font(run, 10.5, bold=True)
    run = paragraph.add_run(
        "视频动作识别；UCF101；时空解耦；帧采样；显存预算；轻量 3D 卷积")
    set_run_font(run, 10.5)
    document.add_page_break()
    add_heading(document, "目录", 1)
    add_paragraph(document, "[[TOC]]", first_line=False)
    document.add_page_break()


def add_audit_section(document):
    add_heading(document, "1 项目审查结论", 1)
    add_paragraph(
        document,
        "重审结果表明，正式代码、数据切分、三种子结果和图表能够相互追溯。"
        "旧五视频演示只保留为系统链路验证，未进入正式精度表。当前核心任务已经完成，"
        "满足题目列出的四项研究内容。"
    )
    add_table(
        document,
        "表 1 A11 要求核对",
        ["要求", "结论", "证据"],
        [
            ["UCF101 与官方切分", "通过", "13320 个 AVI；9537/3783；group 交集 0"],
            ["2D 与轻量 3D 对照", "通过", "TSN-2D、R3D-18、R(2+1)D-18"],
            ["相对基线提升至少 4 个百分点", "通过", "+4.93、+6.34、+7.60 个百分点"],
            ["均匀、稠密、自适应采样", "通过", "固定模型、8 帧、112×112"],
            ["AMP、检查点、梯度累积", "通过", "显存矩阵和端到端短测试"],
            ["Top-1/Top-5、峰值显存、吞吐", "通过", "三种子结果和运行日志"],
            ["至少 3 个训练种子", "通过", "种子 0、1、2"],
            ["类别错误归因", "通过", "101×101 混淆矩阵与分类别召回"],
            ["时空投入优先级结论", "通过", "空间优先 84.19%；时间优先 61.71%"],
        ],
        [1.7, 0.9, 4.0],
    )
    add_paragraph(
        document,
        "需要明确的范围是：主实验采用冻结的 Kinetics-400 预训练主干，只训练分类头或"
        "时序聚合头。它是资源受限迁移训练，不等同于端到端全网络微调。该限制不影响"
        "题目要求的路线、采样、显存和错误归因实验，但应作为答辩中的边界说明。"
    )


def add_task_section(document):
    add_heading(document, "2 问题重述与研究目标", 1, page_break=True)
    add_heading(document, "2.1 研究背景", 2)
    add_paragraph(
        document,
        "视频动作识别需要同时利用空间外观和时间运动。直接使用高容量三维卷积可以联合"
        "建模时空关系，但激活和参数规模较大。二维骨干结合帧级特征与视频级聚合可以复用"
        "空间预训练权重，并通过共享编码器控制计算量。本文在真实 4 GiB 显卡上把训练"
        "显存限制在 2 GiB，以内比较不同时空路线。"
    )
    add_heading(document, "2.2 研究内容", 2)
    add_bullets(document, [
        "比较 TSN 式二维时序聚合、朴素 R3D-18 和轻量 R(2+1)D-18。",
        "在固定模型、帧数和分辨率下比较均匀、稠密与运动自适应采样。",
        "验证 AMP、梯度检查点与梯度累积的显存效果。",
        "生成分类别错误归因，并回答时间维与空间维的投入优先级。",
    ])
    add_heading(document, "2.3 验收指标", 2)
    add_paragraph(
        document,
        "主指标为官方测试集 3783 个视频的 Top-1，辅助指标为 Top-5。候选相对 R3D-18 "
        "必须至少提高 4 个百分点。每个核心头部配置使用种子 0、1、2，并记录样本标准差、"
        "同种子配对差值、显存峰值和吞吐。"
    )


def add_data_section(document):
    add_heading(document, "3 数据与实验协议", 1)
    add_table(
        document,
        "表 2 UCF101 数据完整性",
        ["检查项", "结果"],
        [
            ["期望与实际视频数", f"{DATA['expected_videos']} / {DATA['actual_videos']}"],
            ["类别数", str(DATA["classes_actual"])],
            ["缺失、大小错误、解码失败", "0 / 0 / 0"],
            ["官方训练 / 测试", f"{SPLIT['train_videos']} / {SPLIT['test_videos']}"],
            ["训练拟合 / 验证", f"{SPLIT['train_fit_videos']} / {SPLIT['validation_videos']}"],
            ["训练、验证、测试 group 交集", str(SPLIT["group_overlap"])],
        ],
        [3.2, 2.8],
    )
    add_paragraph(
        document,
        "主实验使用官方 split 1。为避免同一演员或场景同时出现在训练和验证中，从官方"
        "训练集按类别固定留出两个 group 作为验证集，测试集只用于最终评估。"
    )
    add_equation(document, "group_disjoint", 1)
    add_figure(
        document,
        "figures/dataset_class_distribution.png",
        "图 1 UCF101 分类别视频数量",
        6.2,
    )
    add_heading(document, "3.1 统一输入与比较口径", 2)
    add_table(
        document,
        "表 3 主实验配置",
        ["路线", "主干", "时序表示", "预训练"],
        [
            ["TSN-2D", "ResNet-50", "逐帧特征 + 均值/时序注意力", "Kinetics-400"],
            ["朴素 3D", "R3D-18", "三维联合卷积 + 全局池化", "Kinetics-400"],
            ["轻量 3D", "R(2+1)D-18", "空间/时间分解卷积", "Kinetics-400"],
        ],
        [1.15, 1.15, 2.7, 1.35],
    )
    add_paragraph(
        document,
        "三条主路线统一使用 8 帧、112×112、101 类输出和相同测试切分。批大小依据每个"
        "模型的单步内存预检单独设置。这里比较的是同一个 2 GiB 硬上限下的可实现性，"
        "并不要求三条模型达到完全相同的实际占用。"
    )


def add_method_section(document):
    add_heading(document, "4 时空解耦模型", 1)
    add_figure(
        document,
        "figures/fig_model.png",
        "图 2 三条候选路线与分类头结构",
        6.3,
    )
    add_heading(document, "4.1 TSN 式二维聚合", 2)
    add_paragraph(
        document,
        "将视频时间轴等分为 K 段，每段采样一帧并由共享二维 ResNet-50 编码。视频表示"
        "采用平均池化或位置感知时序注意力。时序注意力先把帧特征投影到 256 维，加入"
        "可学习位置编码，再经过两层 Transformer 编码器。"
    )
    add_equation(document, "tsn_pool", 2)
    add_heading(document, "4.2 朴素三维基线", 2)
    add_paragraph(
        document,
        "R3D-18 直接处理 8 帧三维张量，以三维卷积联合学习空间与时间模式，并在最后"
        "进行全局时空池化和线性分类。该路线是题目要求的朴素 3D-CNN 参照。"
    )
    add_heading(document, "4.3 轻量时空分解", 2)
    add_paragraph(
        document,
        "R(2+1)D-18 把三维卷积分解为空间二维卷积和时间一维卷积。分解增加中间非线性，"
        "但降低单个三维卷积的耦合程度，使空间外观和时间运动可以分别建模。"
    )
    add_equation(document, "r21d", 3)
    add_heading(document, "4.4 训练目标", 2)
    add_paragraph(
        document,
        "分类头使用多类交叉熵和 AdamW 优化，学习率余弦退火，共训练 80 轮。验证集"
        "按 Top-1 选择最佳轮次，最终只在该轮次评估官方测试集。"
    )


def add_resource_section(document):
    add_heading(document, "5 资源约束与帧采样", 1)
    add_heading(document, "5.1 2 GiB 双峰值门禁", 2)
    add_paragraph(
        document,
        "每个训练或特征提取进程同时监测 allocator 已分配和预留显存。只有两个峰值都不"
        "超过 2048 MiB 才视为可行。超过上限的进程立即终止，其结果不进入可行配置表。"
    )
    add_equation(document, "memory_budget", 4)
    add_heading(document, "5.2 三种采样", 2)
    add_paragraph(
        document,
        "均匀采样把视频分为 K 段，每段在中心附近取样。稠密采样在连续窗口中每隔 d 帧"
        "取一帧。自适应采样先解码 32 个候选帧，计算灰度帧差运动强度，再按运动强度和"
        "时间多样性选择 K 帧。候选解码与评分时间作为单独成本记录。"
    )
    add_heading(document, "5.3 显存技术", 2)
    add_paragraph(
        document,
        "AMP 使用 FP16 前向与反向计算，并保留 FP32 主权重和损失缩放。梯度检查点只保存"
        "模块边界，在反向传播时重算中间激活。梯度累积通过多个小批量构造等效较大批量。"
        "端到端训练入口在真实 UCF101 视频上完成过前向、反向、累积和保存测试。"
    )
    add_heading(document, "5.4 等成本时间与空间", 2)
    add_paragraph(
        document,
        "时间优先使用 16×64×64，空间优先使用 4×128×128。两者每视频均为 65536 个"
        "空间像素帧，批大小均为 8。均衡配置使用主实验的 8×112×112。"
    )
    add_equation(document, "equal_cost", 5)


def add_results_section(document):
    add_heading(document, "6 正式实验结果", 1)
    main_rows = [
        AGG[("main", "r3d18_uniform", "linear")],
        AGG[("main", "tsn2d_uniform", "linear")],
        AGG[("main", "tsn2d_uniform", "temporal")],
        AGG[("main", "r2plus1d18_uniform", "linear")],
    ]
    add_table(
        document,
        "表 4 三条主路线正式结果",
        ["路线", "Top-1", "Top-5", "头部峰值", "特征吞吐"],
        [
            ["R3D-18 基线", pm(main_rows[0], "top1"),
             pm(main_rows[0], "top5"),
             f"{main_rows[0]['max_peak_mib']:.0f} MiB",
             f"{main_rows[0]['feature_throughput']:.2f} video/s"],
            ["TSN-2D 线性", pm(main_rows[1], "top1"),
             pm(main_rows[1], "top5"),
             f"{main_rows[1]['max_peak_mib']:.0f} MiB",
             f"{main_rows[1]['feature_throughput']:.2f} video/s"],
            ["TSN-2D 时序注意力", pm(main_rows[2], "top1"),
             pm(main_rows[2], "top5"),
             f"{main_rows[2]['max_peak_mib']:.0f} MiB",
             f"{main_rows[2]['feature_throughput']:.2f} video/s"],
            ["R(2+1)D-18", pm(main_rows[3], "top1"),
             pm(main_rows[3], "top5"),
             f"{main_rows[3]['max_peak_mib']:.0f} MiB",
             f"{main_rows[3]['feature_throughput']:.2f} video/s"],
        ],
        [1.55, 1.15, 1.15, 1.0, 1.35],
        highlight_row=4,
    )
    add_figure(
        document,
        "figures/main_route_accuracy.png",
        "图 3 三条主路线的 Top-1 与 Top-5",
        6.2,
    )
    add_paragraph(
        document,
        "TSN 线性头达到 81.29%，时序注意力提高到 82.70%。R(2+1)D-18 取得最高 Top-1 "
        "83.97%，但特征提取吞吐只有 22.20 video/s。二维 TSN 路线吞吐为 52.98 "
        "video/s，适合对延迟更敏感的应用。"
    )
    comparisons = [
        COMP[("tsn2d_uniform", "linear")],
        COMP[("tsn2d_uniform", "temporal")],
        COMP[("r2plus1d18_uniform", "linear")],
    ]
    add_table(
        document,
        "表 5 候选相对 R3D-18 的同种子配对差值",
        ["候选", "提升/百分点", "差值标准差", "配对 p 值"],
        [
            ["TSN-2D 线性",
             f"{comparisons[0]['delta_mean'] * 100:.2f}",
             f"{comparisons[0]['delta_std'] * 100:.2f}",
             f"{comparisons[0]['paired_p_value']:.4f}"],
            ["TSN-2D 时序注意力",
             f"{comparisons[1]['delta_mean'] * 100:.2f}",
             f"{comparisons[1]['delta_std'] * 100:.2f}",
             f"{comparisons[1]['paired_p_value']:.4f}"],
            ["R(2+1)D-18",
             f"{comparisons[2]['delta_mean'] * 100:.2f}",
             f"{comparisons[2]['delta_std'] * 100:.2f}",
             f"{comparisons[2]['paired_p_value']:.4f}"],
        ],
        [2.2, 1.4, 1.4, 1.2],
    )
    add_paragraph(
        document,
        "三项候选均超过 4 个百分点目标，对应提升分别为 4.93、6.34 和 7.60 个百分点。"
        "由于只有三个训练种子，配对检验 p 值仅作辅助描述，不作为大样本显著性保证。"
    )
    add_figure(
        document,
        "figures/main_delta_vs_r3d.png",
        "图 4 候选路线相对 R3D-18 的绝对 Top-1 提升",
        5.8,
    )

    uniform = AGG[("main", "tsn2d_uniform", "temporal")]
    dense = AGG[("sampling", "tsn2d_dense", "temporal")]
    adaptive = AGG[("sampling", "tsn2d_adaptive", "temporal")]
    add_heading(document, "6.1 帧采样消融", 2)
    add_table(
        document,
        "表 6 固定 TSN-2D 的采样策略消融",
        ["策略", "Top-1", "Top-5", "吞吐", "额外评分时间"],
        [
            ["均匀分段", pm(uniform, "top1"), pm(uniform, "top5"),
             f"{uniform['feature_throughput']:.2f} video/s", "0 s"],
            ["连续稠密", pm(dense, "top1"), pm(dense, "top5"),
             f"{dense['feature_throughput']:.2f} video/s", "0 s"],
            ["运动自适应", pm(adaptive, "top1"), pm(adaptive, "top5"),
             f"{adaptive['feature_throughput']:.2f} video/s",
             f"{adaptive['feature_adaptive_score_seconds']:.2f} s"],
        ],
        [1.4, 1.25, 1.25, 1.35, 1.35],
        highlight_row=1,
    )
    add_figure(
        document,
        "figures/sampling_comparison.png",
        "图 5 均匀、稠密与自适应采样的 Top-1",
        6.0,
    )
    add_paragraph(
        document,
        "连续稠密比均匀分段低 4.10 个百分点。自适应采样接近均匀采样，但 3783 个测试"
        "视频共解码 121056 个候选帧，额外评分 196.30 秒，吞吐降至 16.84 video/s。"
    )
    add_heading(document, "6.2 显存优化", 2)
    add_figure(
        document,
        "figures/memory_efficiency.png",
        "图 6 AMP 与梯度检查点的显存峰值",
        6.4,
    )
    add_table(
        document,
        "表 7 代表性显存消融",
        ["配置", "allocated/MiB", "reserved/MiB"],
        [
            ["TSN FP32", f"{MEM['tsn_fp32']['max_memory_allocated_mib']:.2f}",
             f"{MEM['tsn_fp32']['max_memory_reserved_mib']:.0f}"],
            ["TSN AMP", f"{MEM['tsn_amp']['max_memory_allocated_mib']:.2f}",
             f"{MEM['tsn_amp']['max_memory_reserved_mib']:.0f}"],
            ["TSN AMP + 检查点",
             f"{MEM['tsn_amp_checkpoint']['max_memory_allocated_mib']:.2f}",
             f"{MEM['tsn_amp_checkpoint']['max_memory_reserved_mib']:.0f}"],
            ["R3D FP32", f"{MEM['r3d_fp32']['max_memory_allocated_mib']:.2f}",
             f"{MEM['r3d_fp32']['max_memory_reserved_mib']:.0f}"],
            ["R2+1D FP32", f"{MEM['r2plus_fp32']['max_memory_allocated_mib']:.2f}",
             f"{MEM['r2plus_fp32']['max_memory_reserved_mib']:.0f}"],
        ],
        [2.5, 1.8, 1.8],
    )
    add_heading(document, "6.3 时间与空间投入", 2)
    time_row = AGG[("budget", "budget_time_k16_r64", "temporal")]
    space_row = AGG[("budget", "budget_space_k4_r128", "temporal")]
    add_table(
        document,
        "表 8 等成本时间与空间预算",
        ["配置", "输入", "Top-1", "Top-5", "特征峰值", "吞吐"],
        [
            ["时间优先", "16×64×64", pm(time_row, "top1"),
             pm(time_row, "top5"),
             f"{time_row['feature_peak_mib']:.0f} MiB",
             f"{time_row['feature_throughput']:.2f}"],
            ["空间优先", "4×128×128", pm(space_row, "top1"),
             pm(space_row, "top5"),
             f"{space_row['feature_peak_mib']:.0f} MiB",
             f"{space_row['feature_throughput']:.2f}"],
        ],
        [1.1, 1.1, 1.15, 1.15, 1.05, 0.9],
        highlight_row=2,
    )
    add_figure(
        document,
        "figures/time_space_budget.png",
        "图 7 等成本时间与空间优先结果",
        6.0,
    )
    add_paragraph(
        document,
        "空间优先比时间优先高 22.48 个百分点，且特征提取显存更低、吞吐更高。时间优先"
        "的 16 帧时序头训练 reserved 峰值为 1912 MiB，接近上限。结果表明，在本数据与"
        "冻结预训练协议下，空间分辨率是更有效的预算投入方向。"
    )


def add_error_section(document):
    add_heading(document, "7 类别错误归因", 1, page_break=True)
    add_paragraph(
        document,
        "采用最佳 R(2+1)D-18 的种子 0 测试预测生成 101×101 混淆矩阵。按动作语义把"
        "类别分为人际交互、人体动作、物体交互、演奏乐器和体育运动五组，该分组用于"
        "解释错误结构，不替代官方标签。"
    )
    add_figure(
        document,
        "results/feature_pipeline/main_20261125_193324/"
        "error_analysis/r2plus1d18/confusion_matrix.png",
        "图 8 R(2+1)D-18 的 101 类归一化混淆矩阵",
        4.8,
    )
    add_paragraph(
        document,
        "主要混淆对包括 BrushingTeeth 与 ShavingBeard、YoYo 与 Archery/JugglingBalls、"
        "BoxingPunchingBag 与 BoxingSpeedBag、FrontCrawl 与 BreastStroke、以及 "
        "CricketShot 与 CricketBowling。错误集中在面部近景、细长物体轨迹、相近场景"
        "和相似周期动作。"
    )
    add_figure(
        document,
        "results/feature_pipeline/main_20261125_193324/"
        "error_analysis/r2plus1d18/action_group_accuracy.png",
        "图 9 动作语义组的测试准确率",
        5.9,
    )
    group_map = {
        row["group"]: row["accuracy"] for row in ERROR["action_groups"]
    }
    add_table(
        document,
        "表 9 动作语义组归因",
        ["动作组", "类数", "支持样本", "准确率"],
        [
            [row["group"], str(row["class_count"]), str(row["support"]),
             pct(row["accuracy"])]
            for row in ERROR["action_groups"]
        ],
        [1.8, 0.9, 1.1, 1.1],
    )
    add_paragraph(
        document,
        "人体动作组只有 67.78%，明显低于演奏乐器的 94.76% 和人际交互的 92.05%。"
        "最低召回类别为 YoYo、Lunges、HandstandWalking、Hammering 和 "
        "CricketBowling。"
    )
    add_figure(
        document,
        "results/feature_pipeline/main_20261125_193324/"
        "error_analysis/r2plus1d18/examples/error_01.jpg",
        "图 10 代表性错误案例",
        4.6,
    )


def add_evaluation_section(document):
    add_heading(document, "8 模型评价与结论", 1)
    add_heading(document, "8.1 是否满足题目要求", 2)
    add_paragraph(
        document,
        "题目要求的三条路线对照、三种采样、显存优化、Top-1/Top-5、至少三个训练种子、"
        "101 类错误归因和时空优先级均已实现。2D 路线两种头部和轻量 3D 路线均达到"
        "相对 R3D-18 提升至少 4 个百分点的目标。所有正式训练与提取均未超过 2 GiB。"
    )
    add_heading(document, "8.2 主要结论", 2)
    add_bullets(document, [
        "R(2+1)D-18 取得最高 Top-1 83.97%，但吞吐低于二维路线。",
        "TSN 时序注意力达到 82.70%，在精度和吞吐之间更均衡。",
        "连续稠密采样比均匀分段低 4.10 个百分点。",
        "自适应采样未产生正精度收益，并显著增加预处理成本。",
        "等成本下空间优先达到 84.19%，时间优先为 61.71%。",
    ])
    add_heading(document, "8.3 局限与改进", 2)
    add_paragraph(
        document,
        "主实验采用冻结预训练主干，不包含全网络端到端微调。模型容量、预训练来源和"
        "批大小并不完全相等，因此本文把差异解释为资源上限内的路线可实现性，而不把"
        "全部精度差归因于单一因素。未来可增加局部微调、多 split 验证、光流或轻量"
        "时序卷积，并继续维持相同显存上限。"
    )
    add_heading(document, "8.4 推广", 2)
    add_paragraph(
        document,
        "双峰值显存门禁、固定输入成本、同种子配对比较和额外预处理成本单列的方法，"
        "可以用于课堂行为识别、工业操作合规检测、体育动作分析和跌倒监测。二维路线"
        "适合在线推断，轻量三维路线适合事件后的高精度复核。"
    )


def add_references_and_appendix(document):
    add_heading(document, "9 参考文献", 1, page_break=True)
    references = [
        "Wang L, Xiong Y, Wang Z, et al. Temporal segment networks: Towards good "
        "practices for deep action recognition. ECCV, 2016: 20-36.",
        "Carreira J, Zisserman A. Quo vadis, action recognition? A new model and "
        "the Kinetics dataset. CVPR, 2017: 6299-6308.",
        "Soomro K, Zamir A R, Shah M. UCF101: A dataset of 101 human action "
        "classes from videos in the wild. CRCV-TR-12-01, 2012.",
        "Tran D, Wang H, Torresani L, et al. A closer look at spatiotemporal "
        "convolutions for action recognition. CVPR, 2018: 6450-6459.",
        "Kay W, Carreira J, Simonyan K, et al. The Kinetics human action video "
        "dataset. arXiv:1705.06950, 2017.",
        "Micikevicius P, Narang S, Alben J, et al. Mixed precision training. "
        "ICLR, 2018.",
        "Chen T, Xu B, Zhang C, et al. Training deep nets with sublinear memory "
        "cost. arXiv:1604.06174, 2016.",
        "Loshchilov I, Hutter F. Decoupled weight decay regularization. ICLR, "
        "2019.",
    ]
    for index, reference in enumerate(references, start=1):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.left_indent = Pt(18)
        paragraph.paragraph_format.first_line_indent = Pt(-18)
        paragraph.paragraph_format.space_after = Pt(5)
        run = paragraph.add_run(f"[{index}] {reference}")
        set_run_font(run, 9.5)

    add_heading(document, "10 附录 核心实现与复现", 1)
    add_paragraph(document, "正式实验一键入口：", first_line=False)
    code = document.add_paragraph()
    code.paragraph_format.left_indent = Inches(0.25)
    code.paragraph_format.space_after = Pt(7)
    run = code.add_run(
        "powershell -ExecutionPolicy Bypass -File .\\run_full_experiment.ps1")
    set_run_font(run, 8.8)

    add_paragraph(document, "2 GiB 硬门禁：", first_line=False)
    for line in (
            "peak_allocated = torch.cuda.max_memory_allocated() / (1024**2)",
            "peak_reserved = torch.cuda.max_memory_reserved() / (1024**2)",
            "if peak_allocated > 2048 or peak_reserved > 2048:",
            "    raise RuntimeError('2 GiB memory budget exceeded')"):
        paragraph = document.add_paragraph()
        paragraph.paragraph_format.left_indent = Inches(0.25)
        paragraph.paragraph_format.space_after = Pt(0)
        run = paragraph.add_run(line)
        set_run_font(run, 8.8)

    add_paragraph(document, "复现材料：", first_line=False, before=8)
    add_bullets(document, [
        "正式结果矩阵与三种子汇总表。",
        "显存消融日志与峰值数据。",
        "分类别预测、混淆矩阵和代表性错误案例。",
        "可复现代码、运行说明与答辩材料。",
    ])


def main():
    document = Document()
    configure_document(document)
    document.core_properties.title = "资源约束下的视频动作识别时空解耦建模"
    document.core_properties.subject = "A11 技术研究报告"
    document.core_properties.author = "Trauma"
    document.core_properties.keywords = (
        "视频动作识别, UCF101, 时空解耦, 帧采样, 显存预算")

    add_cover(document)
    add_abstract(document)
    add_audit_section(document)
    add_task_section(document)
    add_data_section(document)
    add_method_section(document)
    add_resource_section(document)
    add_results_section(document)
    add_error_section(document)
    add_evaluation_section(document)
    add_references_and_appendix(document)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
