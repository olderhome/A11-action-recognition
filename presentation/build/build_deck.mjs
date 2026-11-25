import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const BUILD_DIR = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(BUILD_DIR, "../..");
const PREVIEW_DIR = path.join(PROJECT_ROOT, "presentation", "previews");
const OUTPUT_DIR = path.join(PROJECT_ROOT, "deliverables");
const SKILL_DIR =
  "C:/Users/Administrator/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations";
const FINAL_PPTX = path.join(OUTPUT_DIR, "A11_答辩汇报_终版.pptx");
const STAGING_DIR = path.join(PROJECT_ROOT, ".codex-finalizer");
const RUNTIME_PYTHON =
  "C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe";
process.env.RUNTIME_NODE_MODULES =
  "C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";

const COLORS = {
  paper: "#F7F5EF",
  ink: "#14213D",
  body: "#46505D",
  muted: "#7B8188",
  teal: "#1B7F79",
  tealSoft: "#DDEBE8",
  orange: "#C66A31",
  orangeSoft: "#F4E2D5",
  white: "#FFFFFF",
  line: "#D9D5CA",
  greenSoft: "#DFF0E7",
};
const FONT = "Microsoft YaHei";

const readJson = async (file) =>
  JSON.parse(await fs.readFile(path.join(PROJECT_ROOT, file), "utf8"));
const asset = (file) => path.join(PROJECT_ROOT, file);
const rounded = (value, digits = 4) =>
  Number(Number(value).toFixed(digits));

async function addText(
  slide,
  {
    text,
    left,
    top,
    width,
    height,
    size = 20,
    color = COLORS.body,
    bold = false,
    align = "left",
    valign = "top",
    lineSpacing = 1.15,
  },
) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: FONT,
    fontSize: size,
    bold,
    color,
    alignment: align,
    verticalAlignment: valign,
    lineSpacing,
    wrap: "square",
    insets: 0,
  };
  return shape;
}

function addPageNumber(slide, number) {
  addText(slide, {
    text: String(number).padStart(2, "0"),
    left: 1178,
    top: 682,
    width: 42,
    height: 20,
    size: 12,
    color: COLORS.muted,
    align: "right",
  });
}

function addBaseSlide(presentation, title, number) {
  const slide = presentation.slides.add();
  slide.background.fill = COLORS.paper;
  addText(slide, {
    text: title,
    left: 72,
    top: 42,
    width: 1136,
    height: 72,
    size: 34,
    color: COLORS.ink,
    bold: true,
    valign: "middle",
    lineSpacing: 1.0,
  });
  const rule = slide.shapes.add({
    geometry: "rect",
    position: { left: 72, top: 120, width: 76, height: 4 },
    fill: COLORS.teal,
    line: { style: "solid", fill: "none", width: 0 },
  });
  rule.name = "title-rule";
  addPageNumber(slide, number);
  return slide;
}

function addMetric(slide, left, top, width, value, label, color) {
  addText(slide, {
    text: value,
    left,
    top,
    width,
    height: 52,
    size: 32,
    color,
    bold: true,
    align: "center",
    valign: "middle",
  });
  addText(slide, {
    text: label,
    left,
    top: top + 54,
    width,
    height: 34,
    size: 16,
    color: COLORS.muted,
    align: "center",
  });
}

function styleTable(table, headerFill = COLORS.ink, highlightRow = -1) {
  table.borders.assign({
    style: "solid",
    fill: COLORS.line,
    width: 1,
  });
  for (let row = 0; row < table.rows.length; row += 1) {
    table.rows[row].height = row === 0 ? 44 : 52;
    for (let col = 0; col < table.columns.length; col += 1) {
      const cell = table.getCell(row, col);
      cell.text.style = {
        typeface: FONT,
        fontSize: row === 0 ? 16 : 17,
        bold: row === 0 || row === highlightRow,
        color: row === 0 ? COLORS.white : COLORS.ink,
        verticalAlignment: "middle",
        alignment: col === 0 ? "left" : "center",
        insets: { left: 10, right: 10, top: 4, bottom: 4 },
      };
      if (row === 0) cell.fill = headerFill;
      else if (row === highlightRow) cell.fill = COLORS.greenSoft;
      else cell.fill = row % 2 ? "#FBFAF6" : COLORS.white;
    }
  }
}

function chartTextStyle(size = 14, bold = false) {
  return {
    typeface: FONT,
    fontSize: size,
    bold,
    fill: COLORS.body,
  };
}

async function addImage(slide, file, position, alt, fit = "contain") {
  const bytes = await fs.readFile(asset(file));
  return slide.images.add({
    blob: new Uint8Array(bytes),
    contentType: file.toLowerCase().endsWith(".png")
      ? "image/png"
      : "image/jpeg",
    alt,
    fit,
    position,
  });
}

async function main() {
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  await fs.mkdir(STAGING_DIR, { recursive: true });

  const summary = await readJson(
    "results/feature_pipeline/main_20261125_193324/summary/summary.json",
  );
  const memory = await readJson(
    "results/memory/memory_20261125_173351/matrix.json",
  );
  const dataAudit = await readJson(
    "results/data/ucf101_dataset_validation.json",
  );
  const split = await readJson("results/data/ucf101_split1_summary.json");
  const error = await readJson(
    "results/feature_pipeline/main_20261125_193324/error_analysis/r2plus1d18/error_summary.json",
  );
  const aggregates = summary.aggregate;
  const byKey = new Map(
    aggregates.map((row) => [`${row.suite}:${row.config}:${row.probe_type}`, row]),
  );
  const comps = new Map(
    summary.comparisons.map((row) => [`${row.candidate}:${row.candidate_probe}`, row]),
  );

  const mainRows = [
    byKey.get("main:r3d18_uniform:linear"),
    byKey.get("main:tsn2d_uniform:linear"),
    byKey.get("main:tsn2d_uniform:temporal"),
    byKey.get("main:r2plus1d18_uniform:linear"),
  ];
  const best = [...mainRows].sort((a, b) => b.top1_mean - a.top1_mean)[0];

  const presentation = Presentation.create({
    slideSize: { width: 1280, height: 720 },
  });
  presentation.theme.defaultFont = FONT;

  // 1. Cover
  {
    const slide = presentation.slides.add();
    slide.background.fill = COLORS.ink;
    addText(slide, {
      text: "A11 技术研究",
      left: 76,
      top: 58,
      width: 280,
      height: 28,
      size: 16,
      color: "#A9C9C5",
      bold: true,
    });
    addText(slide, {
      text: "资源约束下的视频动作识别\n时空解耦建模",
      left: 76,
      top: 156,
      width: 1000,
      height: 150,
      size: 46,
      color: COLORS.white,
      bold: true,
      valign: "middle",
      lineSpacing: 1.08,
    });
    addText(slide, {
      text: "UCF101 · 101 类 · 训练显存不超过 2 GiB",
      left: 80,
      top: 352,
      width: 760,
      height: 42,
      size: 22,
      color: "#C9D5D9",
    });
    const accent = slide.shapes.add({
      geometry: "rect",
      position: { left: 80, top: 430, width: 188, height: 5 },
      fill: COLORS.orange,
      line: { style: "solid", fill: "none", width: 0 },
    });
    accent.name = "cover-accent";
    addText(slide, {
      text: "答辩汇报  |  2026 年 11 月",
      left: 80,
      top: 470,
      width: 560,
      height: 32,
      size: 17,
      color: "#AEB8BD",
    });
    slide.speakerNotes.text =
      "开场先说明研究对象是资源约束下的视频动作识别。强调本项目的关键不是单纯堆叠模型，而是在 UCF101、官方切分和 2 GiB 硬预算下做可复核的路线对照。";
  }

  // 2. Requirements
  {
    const slide = addBaseSlide(presentation, "题目要求与验收指标", 2);
    const rows = [
      ["研究内容", "本项目验收口径"],
      ["路线对照", "TSN-2D、R3D-18、R(2+1)D-18"],
      ["帧采样消融", "固定模型与输入成本，比较均匀、稠密、自适应"],
      ["显存优化", "AMP、检查点、梯度累积，双峰值不超过 2048 MiB"],
      ["错误归因", "101 类混淆矩阵、分类别召回、代表性冲突"],
      ["核心目标", "相对朴素 R3D-18 的 Top-1 提升至少 4 个百分点"],
    ];
    const table = slide.tables.add({
      rows: rows.length,
      columns: 2,
      left: 72,
      top: 164,
      width: 1136,
      height: 404,
      values: rows,
      columnWidths: [250, 886],
    });
    styleTable(table, COLORS.ink, 5);
    addText(slide, {
      text: "验收同时要求官方 split 1、3 个训练种子、Top-1/Top-5、全量测试和可追溯结果",
      left: 72,
      top: 602,
      width: 1136,
      height: 42,
      size: 18,
      color: COLORS.teal,
      bold: true,
      align: "center",
    });
    slide.speakerNotes.text =
      "这页先把评委关心的验收条件说清楚。后续每一页都围绕这些条件给出对应证据，正式结论只使用 3783 个官方测试视频。";
  }

  // 3. Data integrity
  {
    const slide = addBaseSlide(presentation, "UCF101 数据与官方切分", 3);
    addMetric(slide, 72, 168, 210, String(dataAudit.actual_videos), "完整 AVI", COLORS.ink);
    addMetric(slide, 300, 168, 150, String(dataAudit.classes_actual), "类别", COLORS.teal);
    addMetric(slide, 470, 168, 150, String(split.train_videos), "官方训练", COLORS.ink);
    addMetric(slide, 640, 168, 150, String(split.test_videos), "官方测试", COLORS.orange);
    await addImage(
      slide,
      "figures/dataset_class_distribution.png",
      { left: 72, top: 292, width: 720, height: 314 },
      "UCF101 分类别训练与测试视频数量",
    );
    addText(slide, {
      text: "完整性检查",
      left: 832,
      top: 300,
      width: 320,
      height: 32,
      size: 21,
      color: COLORS.ink,
      bold: true,
    });
    addText(slide, {
      text:
        `缺失文件 ${dataAudit.missing_count}\n` +
        `大小错误 ${dataAudit.size_mismatch_count}\n` +
        `首帧解码失败 ${dataAudit.decode_header_failure_count}\n\n` +
        `训练拟合 ${split.train_fit_videos}\n验证 ${split.validation_videos}\n` +
        `group 交集 ${split.group_overlap}`,
      left: 832,
      top: 348,
      width: 330,
      height: 230,
      size: 19,
      color: COLORS.body,
      lineSpacing: 1.25,
    });
    slide.speakerNotes.text =
      "数据部分强调两点。第一，13320 个视频全部存在并可解码。第二，测试集只用于最终报告，验证集从官方训练集按 group 留出，三个 group 集合交集为 0。";
  }

  // 4. Model routes
  {
    const slide = addBaseSlide(presentation, "三条时空建模路线", 4);
    await addImage(
      slide,
      "figures/fig_model.png",
      { left: 94, top: 150, width: 1092, height: 520 },
      "TSN-2D、R3D-18 与 R(2+1)D-18 模型路线",
    );
    slide.speakerNotes.text =
      "二维路线把空间编码与时间聚合分开。R3D-18 是朴素三维基线。R(2+1)D-18 把三维卷积拆成空间卷积和时间卷积。三条路线都使用 Kinetics-400 预训练、8 帧和 112 乘 112 输入。";
  }

  // 5. Memory engineering
  {
    const slide = addBaseSlide(presentation, "2 GiB 预算内的显存工程", 5);
    addText(slide, {
      text:
        "同时监测 allocated 与 reserved\n" +
        "硬门禁为 2048 MiB\n" +
        "TSN FP32 的 reserved 峰值为 950 MiB\n" +
        "AMP 降至 610 MiB\n" +
        "加入检查点后降至 428 MiB",
      left: 72,
      top: 170,
      width: 360,
      height: 270,
      size: 20,
      color: COLORS.body,
      lineSpacing: 1.3,
    });
    const selectedNames = [
      "tsn_amp",
      "tsn_amp_checkpoint",
      "tsn_fp32",
      "r3d_amp",
      "r2plus_amp",
      "r2plus_fp32",
    ];
    const selected = selectedNames.map((name) =>
      memory.find((row) => row.name === name),
    );
    slide.charts.add("bar", {
      position: { left: 456, top: 154, width: 740, height: 472 },
      categories: ["TSN AMP", "TSN CP", "TSN FP32", "R3D AMP", "R2+ AMP", "R2+ FP32"],
      series: [
        {
          name: "reserved",
          values: selected.map((row) =>
            rounded(row.max_memory_reserved_mib, 3)),
          fill: COLORS.teal,
        },
      ],
      title: "",
      titlePlacement: "none",
      hasLegend: false,
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 54 },
      yAxis: {
        min: 0,
        max: 1100,
        majorUnit: 250,
        title: { text: "MiB", textStyle: chartTextStyle(13) },
        textStyle: chartTextStyle(13),
        majorGridlines: { style: "solid", fill: COLORS.line, width: 1 },
      },
      xAxis: { textStyle: chartTextStyle(13) },
      dataLabels: {
        showValue: true,
        position: "outEnd",
        textStyle: chartTextStyle(12, true),
      },
    });
    slide.speakerNotes.text =
      "显存预算使用两个 allocator 峰值共同判定。这里展示代表性结果，TSN 的 FP32、AMP 与检查点形成清晰的三级下降。所有正式训练与提取都执行同一 2048 MiB 门禁。";
  }

  // 6. Main results table
  {
    const slide = addBaseSlide(presentation, "正式主结果", 6);
    const names = {
      "main:r3d18_uniform:linear": "R3D-18 基线",
      "main:tsn2d_uniform:linear": "TSN-2D 线性",
      "main:tsn2d_uniform:temporal": "TSN-2D 时序注意力",
      "main:r2plus1d18_uniform:linear": "R(2+1)D-18",
    };
    const values = [
      ["路线", "Top-1", "Top-5", "训练峰值", "特征吞吐"],
      ...mainRows.map((row) => [
        names[`${row.suite}:${row.config}:${row.probe_type}`],
        `${(row.top1_mean * 100).toFixed(2)} ± ${(row.top1_std * 100).toFixed(2)}%`,
        `${(row.top5_mean * 100).toFixed(2)}%`,
        `${row.max_peak_mib.toFixed(0)} MiB`,
        `${row.feature_throughput.toFixed(1)} video/s`,
      ]),
    ];
    const table = slide.tables.add({
      rows: values.length,
      columns: 5,
      left: 72,
      top: 164,
      width: 1136,
      height: 374,
      values,
      columnWidths: [310, 210, 160, 210, 246],
    });
    const bestRow = mainRows.findIndex((row) => row === best) + 1;
    styleTable(table, COLORS.ink, bestRow);
    addText(slide, {
      text: "均值和样本标准差来自训练种子 0、1、2",
      left: 72,
      top: 560,
      width: 1136,
      height: 30,
      size: 16,
      color: COLORS.muted,
      align: "center",
    });
    addText(slide, {
      text: `最佳路线：${names[`${best.suite}:${best.config}:${best.probe_type}`]}，Top-1 ${(best.top1_mean * 100).toFixed(2)}%`,
      left: 72,
      top: 604,
      width: 1136,
      height: 38,
      size: 21,
      color: COLORS.teal,
      bold: true,
      align: "center",
    });
    slide.speakerNotes.text =
      "主结果的三条候选路线都使用相同官方测试集。最高的是 R(2+1)D-18，TSN 时序注意力紧随其后，R3D-18 是朴素基线。表中显存和吞吐来自实际运行记录。";
  }

  // 7. Delta target
  {
    const slide = addBaseSlide(presentation, "三条候选配置均超过 4 个百分点目标", 7);
    const deltas = [
      ["TSN 线性", comps.get("tsn2d_uniform:linear").delta_mean * 100],
      ["TSN 时序注意力", comps.get("tsn2d_uniform:temporal").delta_mean * 100],
      ["R(2+1)D-18", comps.get("r2plus1d18_uniform:linear").delta_mean * 100],
    ];
    slide.charts.add("bar", {
      position: { left: 94, top: 162, width: 760, height: 438 },
      categories: deltas.map(([name]) => name),
      series: [
        {
          name: "相对 R3D-18",
          values: deltas.map(([, value]) => rounded(value)),
          fill: COLORS.teal,
        },
      ],
      title: "",
      titlePlacement: "none",
      hasLegend: false,
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 70 },
      yAxis: {
        min: 0,
        max: 9,
        majorUnit: 2,
        title: { text: "百分点", textStyle: chartTextStyle(13) },
        textStyle: chartTextStyle(13),
        majorGridlines: { style: "solid", fill: COLORS.line, width: 1 },
      },
      xAxis: { textStyle: chartTextStyle(14) },
      dataLabels: {
        showValue: true,
        position: "outEnd",
        numberFormatCode: "0.0",
        textStyle: chartTextStyle(13, true),
      },
    });
    addText(slide, {
      text:
        "4 个百分点目标线\n\n" +
        "配对 t 检验\n" +
        `TSN 时序 p=${comps.get("tsn2d_uniform:temporal").paired_p_value.toFixed(4)}\n` +
        `R(2+1)D p=${comps.get("r2plus1d18_uniform:linear").paired_p_value.toFixed(4)}`,
      left: 892,
      top: 190,
      width: 300,
      height: 220,
      size: 19,
      color: COLORS.body,
      lineSpacing: 1.25,
    });
    addText(slide, {
      text: `最高绝对提升 ${deltas[2][1].toFixed(2)} 个百分点`,
      left: 892,
      top: 448,
      width: 300,
      height: 70,
      size: 25,
      color: COLORS.orange,
      bold: true,
      valign: "middle",
    });
    slide.speakerNotes.text =
      "这一段回答题目最硬的指标。TSN 的两种头部和 R2+1D 共三条候选配置都超过 4 个百分点。配对检验只作为辅助证据，三个种子仍是小样本，因此不把它解释成普遍显著性保证。";
  }

  // 8. Sampling
  {
    const slide = addBaseSlide(presentation, "采样策略消融", 8);
    const samplingRows = [
      byKey.get("main:tsn2d_uniform:temporal"),
      byKey.get("sampling:tsn2d_dense:temporal"),
      byKey.get("sampling:tsn2d_adaptive:temporal"),
    ];
    const labels = ["均匀分段", "连续稠密", "运动自适应"];
    slide.charts.add("bar", {
      position: { left: 82, top: 164, width: 710, height: 430 },
      categories: labels,
      series: [
        {
          name: "Top-1",
          values: samplingRows.map((row) =>
            rounded(row.top1_mean * 100, 3)),
          fill: COLORS.orange,
        },
      ],
      title: "",
      titlePlacement: "none",
      hasLegend: false,
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 66 },
      yAxis: {
        min: 70,
        max: 86,
        majorUnit: 4,
        title: { text: "Top-1 / %", textStyle: chartTextStyle(13) },
        textStyle: chartTextStyle(13),
        majorGridlines: { style: "solid", fill: COLORS.line, width: 1 },
      },
      xAxis: { textStyle: chartTextStyle(14) },
      dataLabels: {
        showValue: true,
        position: "outEnd",
        numberFormatCode: "0.0",
        textStyle: chartTextStyle(13, true),
      },
    });
    const adaptive = samplingRows[2];
    addText(slide, {
      text:
        `均匀 ${(samplingRows[0].top1_mean * 100).toFixed(2)}%\n` +
        `稠密 ${(samplingRows[1].top1_mean * 100).toFixed(2)}%\n` +
        `自适应 ${(adaptive.top1_mean * 100).toFixed(2)}%\n\n` +
        `自适应候选帧：32\n候选评分：${adaptive.feature_adaptive_score_seconds.toFixed(2)} s`,
      left: 844,
      top: 184,
      width: 320,
      height: 270,
      size: 20,
      color: COLORS.body,
      lineSpacing: 1.3,
    });
    addText(slide, {
      text: "固定 TSN-2D、8 帧、112×112",
      left: 844,
      top: 484,
      width: 320,
      height: 54,
      size: 18,
      color: COLORS.teal,
      bold: true,
      valign: "middle",
    });
    slide.speakerNotes.text =
      "采样消融只改变帧位置，不改变模型、帧数或空间分辨率。连续稠密采样只覆盖短时窗口，通常低于覆盖全视频的均匀采样。自适应采样需要额外解码 32 个候选帧并计算运动评分。";
  }

  // 9. Time-space budget
  {
    const slide = addBaseSlide(presentation, "等成本下的时间与空间投入", 9);
    const budgetRows = [
      byKey.get("main:tsn2d_uniform:temporal"),
      byKey.get("budget:budget_time_k16_r64:temporal"),
      byKey.get("budget:budget_space_k4_r128:temporal"),
    ];
    const labels = ["均衡 8×112²", "时间 16×64²", "空间 4×128²"];
    slide.charts.add("bar", {
      position: { left: 82, top: 164, width: 720, height: 430 },
      categories: labels,
      series: [
        {
          name: "Top-1",
          values: budgetRows.map((row) =>
            rounded(row.top1_mean * 100, 3)),
          fill: COLORS.ink,
        },
      ],
      title: "",
      titlePlacement: "none",
      hasLegend: false,
      barOptions: { direction: "column", grouping: "clustered", gapWidth: 68 },
      yAxis: {
        min: 70,
        max: 86,
        majorUnit: 4,
        title: { text: "Top-1 / %", textStyle: chartTextStyle(13) },
        textStyle: chartTextStyle(13),
        majorGridlines: { style: "solid", fill: COLORS.line, width: 1 },
      },
      xAxis: { textStyle: chartTextStyle(14) },
      dataLabels: {
        showValue: true,
        position: "outEnd",
        numberFormatCode: "0.0",
        textStyle: chartTextStyle(13, true),
      },
    });
    addText(slide, {
      text:
        "时间优先与空间优先\n保持相同帧像素成本\n\n" +
        `时间 ${(budgetRows[1].top1_mean * 100).toFixed(2)}%\n` +
        `空间 ${(budgetRows[2].top1_mean * 100).toFixed(2)}%\n` +
        `时间 reserved ${budgetRows[1].feature_peak_mib.toFixed(0)} MiB\n` +
        `空间 reserved ${budgetRows[2].feature_peak_mib.toFixed(0)} MiB`,
      left: 844,
      top: 176,
      width: 330,
      height: 310,
      size: 19,
      color: COLORS.body,
      lineSpacing: 1.28,
    });
    const winner = budgetRows[1].top1_mean >= budgetRows[2].top1_mean ? "时间" : "空间";
    addText(slide, {
      text: `预算优先结论：${winner}维边际收益更高`,
      left: 844,
      top: 512,
      width: 330,
      height: 62,
      size: 22,
      color: COLORS.teal,
      bold: true,
      valign: "middle",
    });
    slide.speakerNotes.text =
      "这一页把时间长度和空间分辨率放到相同帧像素成本下。结论按 Top-1、峰值显存和吞吐共同判断，避免用单一准确率掩盖成本。";
  }

  // 10. Error analysis
  {
    const slide = addBaseSlide(presentation, "错误归因与类别差异", 10);
    await addImage(
      slide,
      "results/feature_pipeline/main_20261125_193324/error_analysis/r2plus1d18/confusion_matrix.png",
      { left: 56, top: 154, width: 474, height: 430 },
      "R(2+1)D-18 的 101 类混淆矩阵",
    );
    await addImage(
      slide,
      "results/feature_pipeline/main_20261125_193324/error_analysis/r2plus1d18/action_group_accuracy.png",
      { left: 548, top: 174, width: 640, height: 382 },
      "R(2+1)D-18 的动作语义组准确率",
    );
    const groupMap = new Map(error.action_groups.map((row) => [row.group, row.accuracy]));
    addText(slide, {
      text:
        `人体动作组 ${(groupMap.get("人体动作") * 100).toFixed(1)}%\n` +
        `体育运动组 ${(groupMap.get("体育运动") * 100).toFixed(1)}%\n` +
        `主要混淆：体态相近和器械相近动作`,
      left: 76,
      top: 590,
      width: 1100,
      height: 60,
      size: 18,
      color: COLORS.body,
      align: "center",
    });
    slide.speakerNotes.text =
      "错误归因显示人体动作组明显低于乐器演奏与体育运动组。典型错误发生在外观相似而运动阶段不同的类别，例如投掷、球类击打和相似体态动作。";
  }

  // 11. Demo system
  {
    const slide = addBaseSlide(presentation, "可视化测试台与摄像头输入", 11);
    await addImage(
      slide,
      "outputs/review_20261125/screenshots/dashboard_running.png",
      { left: 68, top: 150, width: 790, height: 474 },
      "两路线动作识别可视化测试台",
      "cover",
    );
    addText(slide, {
      text:
        "本地视频与摄像头输入\n\n" +
        "同屏显示两条路线\n\n" +
        "Top-1、置信度、时延\n\n" +
        "运行记录自动落盘",
      left: 900,
      top: 190,
      width: 280,
      height: 280,
      size: 21,
      color: COLORS.body,
      lineSpacing: 1.35,
    });
    addText(slide, {
      text: "演示权重用于系统链路验证，正式精度以 UCF101 实验为准",
      left: 890,
      top: 530,
      width: 310,
      height: 72,
      size: 16,
      color: COLORS.orange,
      bold: true,
      valign: "middle",
    });
    slide.speakerNotes.text =
      "现场演示可从已有视频开始，也可调用摄像头。测试台用于展示输入、双路线预测和结果落盘。演示模型与正式 UCF101 结果分开表述，避免把 Kinetics 类名当作正式精度。";
  }

  // 12. Conclusion
  {
    const slide = addBaseSlide(presentation, "结论与可交付成果", 12);
    const deltaTs = comps.get("tsn2d_uniform:temporal").delta_mean * 100;
    const deltaR2 = comps.get("r2plus1d18_uniform:linear").delta_mean * 100;
    addText(slide, {
      text:
        `主指标达标\n` +
        `TSN 时序注意力相对 R3D-18 提升 ${deltaTs.toFixed(2)} 个百分点\n` +
        `R(2+1)D-18 提升 ${deltaR2.toFixed(2)} 个百分点\n\n` +
        `工程约束达标\n` +
        "代表性训练配置 reserved 峰值低于 2048 MiB\n\n" +
        `结论\n最佳绝对精度为 ${(best.top1_mean * 100).toFixed(2)}%\n` +
        "二维路线吞吐更高，轻量三维路线精度更高",
      left: 78,
      top: 170,
      width: 720,
      height: 400,
      size: 22,
      color: COLORS.body,
      lineSpacing: 1.38,
    });
    addText(slide, {
      text:
        "可交付\n\n" +
        "可复现代码\nUCF101 正式结果\n图表与错误案例\n论文与答辩材料",
      left: 858,
      top: 184,
      width: 300,
      height: 260,
      size: 20,
      color: COLORS.ink,
      bold: true,
      lineSpacing: 1.35,
    });
    addText(slide, {
      text: "局限：主实验为冻结主干迁移训练，不是全网络端到端微调",
      left: 858,
      top: 500,
      width: 310,
      height: 92,
      size: 17,
      color: COLORS.orange,
      bold: true,
      valign: "middle",
    });
    slide.speakerNotes.text =
      "结论同时报告精度和成本。二维路线推理吞吐高，轻量三维路线在当前冻结特征协议下精度最高。主实验使用冻结主干，答辩时需要主动说明边界。";
  }

  const montage = await presentation.export({
    format: "webp",
    montage: true,
    scale: 1,
  });
  await fs.writeFile(
    path.join(PREVIEW_DIR, "deck-montage.webp"),
    new Uint8Array(await montage.arrayBuffer()),
  );
  for (let index = 0; index < presentation.slides.items.length; index += 1) {
    const png = await presentation.export({
      slide: presentation.slides.items[index],
      format: "png",
      scale: 1,
    });
    await fs.writeFile(
      path.join(PREVIEW_DIR, `slide-${String(index + 1).padStart(2, "0")}.png`),
      new Uint8Array(await png.arrayBuffer()),
    );
  }

  const candidatePath = path.join(STAGING_DIR, "candidate.pptx");
  const candidate = await PresentationFile.exportPptx(presentation);
  await candidate.save(candidatePath);
  const { finalizePresentation } = await import(
    pathToFileURL(
      path.join(SKILL_DIR, "container_tools/artifact_tool_utils.mjs"),
    ).href
  );
  const result = await finalizePresentation({
    explicitTotalSlideCount: 12,
    requiredNativeTableOwnerSlides: [2, 6],
    requiredNativeChartOwnerSlides: [5, 7, 8, 9],
    materializeLiteralChartWorkbooks: true,
    workspaceDir: PROJECT_ROOT,
    candidatePath,
    finalPath: FINAL_PPTX,
    pythonExecutable: RUNTIME_PYTHON,
    integrityValidatorPath: path.join(
      SKILL_DIR,
      "container_tools/inspect_presentation_package_integrity.py",
    ),
    layoutValidatorPath: path.join(
      SKILL_DIR,
      "container_tools/inspect_presentation_layout_geometry.py",
    ),
    layoutArgs: [
      "--expected-slide-size-emu",
      "12192000,6858000",
      "--validate-bullet-geometry",
      "--validate-heading-fit",
      "--require-native-table-slide",
      "2",
      "--require-native-table-slide",
      "6",
    ],
    fontPolicy: {
      basis: "design",
      families: [FONT],
    },
    verifyArtifactToolImport: true,
    receiptPath: path.join(
      STAGING_DIR,
      "A11_答辩汇报_终版.validation.json",
    ),
  });
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
