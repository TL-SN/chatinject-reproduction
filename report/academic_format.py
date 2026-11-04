"""Apply course-report typography and master's-thesis three-line table conventions.

Style references (examined directly from the user's Word samples):
- Opening report: 12 pt Song/TNR body; 14 pt Hei/TNR main headings;
  12 pt Hei/TNR subheadings; 23 pt body leading, 24 pt first indent,
  4 pt paragraph spacing, 2.4 cm page margins.
- Master's thesis: 10.5 pt experimental table text and captions;
  three horizontal rules, no vertical gridlines.
"""
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


CAPTIONS = {
    "表 2-1": "表 2-1  ChatInject 复现实验环境与任务设置",
    "表 2-2": "表 2-2  DeepSeek 模型在 AgentDojo 上的攻击效果",
    "表 2-3": "表 2-3  原论文与本次复现的攻击成功率对比",
    "表 2-4": "表 2-4  不同受试模型上的提示注入攻击效果对比",
}
NOTES = {
    1: "注：除无攻击基线行的三域数据为 Utility 外，其余三域数据均为 ASR；指标单位均为 %。每组攻击以 389 个正式测试组合为分母，另有 21 条可行性校验日志不参与统计。",
    2: "注：结果来自 AgentDojo 基准，所有数字均为 ASR（%）。原论文与本次复现采用不同受试模型，绝对数值不宜直接比较。",
    3: "注：S1 为普通注入，S2 为原生模板 ChatInject，S3/S4 分别为 think/tool 钩子，S5 为普通多轮，S6 为多轮+ChatInject，S7 为外来模板；S1—S7 为 ASR（%），末列为无攻击 Utility（%）。",
}
WIDTHS = [
    [3.0, 13.2],
    [4.25, 2.08, 2.08, 2.08, 2.73, 2.98],
    [2.85, 2.23, 2.30, 1.70, 1.65, 2.85, 2.62],
    [2.9, 1.46, 1.46, 1.46, 1.46, 1.46, 1.46, 1.46, 2.84],
]


def east_asia(item, font):
    rpr = item._element.get_or_add_rPr()
    fonts = rpr.rFonts
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    fonts.set(qn("w:eastAsia"), font)
    fonts.set(qn("w:ascii"), "Times New Roman")
    fonts.set(qn("w:hAnsi"), "Times New Roman")


def set_text_run(run, size, cjk="宋体", bold=None):
    run.font.name = "Times New Roman"
    run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    east_asia(run, cjk)


def set_style(doc, name, size, cjk, spacing, before, after, indent=0, centered=False):
    style = doc.styles[name]
    style.font.name = "Times New Roman"
    style.font.size = Pt(size)
    east_asia(style, cjk)
    fmt = style.paragraph_format
    fmt.line_spacing = Pt(spacing)
    fmt.space_before = Pt(before)
    fmt.space_after = Pt(after)
    fmt.first_line_indent = Pt(indent)
    if name != "真文本正文":
        fmt.keep_with_next = True
    if centered:
        fmt.alignment = WD_ALIGN_PARAGRAPH.CENTER


def border_cell(cell, top=None, bottom=None):
    pr = cell._tc.get_or_add_tcPr()
    borders = pr.find(qn("w:tcBorders"))
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        pr.append(borders)
    for side in ("top", "bottom", "left", "right"):
        e = borders.find(qn("w:" + side))
        if e is None:
            e = OxmlElement("w:" + side)
            borders.append(e)
        width = top if side == "top" else bottom if side == "bottom" else None
        if width:
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), str(width))
            e.set(qn("w:color"), "000000")
        else:
            e.set(qn("w:val"), "nil")
            if e.get(qn("w:sz")) is not None:
                del e.attrib[qn("w:sz")]


def border_table(table):
    pr = table._tbl.tblPr
    bd = pr.find(qn("w:tblBorders"))
    if bd is None:
        bd = OxmlElement("w:tblBorders")
        pr.append(bd)
    for side in ("top", "bottom", "insideH", "insideV", "left", "right"):
        e = bd.find(qn("w:" + side))
        if e is None:
            e = OxmlElement("w:" + side)
            bd.append(e)
        if side in ("top", "bottom"):
            e.set(qn("w:val"), "single")
            e.set(qn("w:sz"), "12")
            e.set(qn("w:color"), "000000")
        else:
            e.set(qn("w:val"), "nil")


def add_note(table, text):
    element = OxmlElement("w:p")
    table._tbl.addnext(element)
    para = Paragraph(element, table._parent)
    f = para.paragraph_format
    f.first_line_indent = Pt(0)
    f.space_before = Pt(3)
    f.space_after = Pt(5)
    f.line_spacing = 1.15
    set_text_run(para.add_run(text), 9.5)


def apply_academic_format(doc):
    for sec in doc.sections:
        sec.left_margin = Cm(2.4)
        sec.right_margin = Cm(2.4)
        sec.top_margin = Cm(2.4)
        sec.bottom_margin = Cm(2.4)

    set_style(doc, "真文本正文", 12, "宋体", 23, 0, 4, indent=24)
    set_style(doc, "一级标题", 14, "黑体", 24, 9, 5, centered=True)
    set_style(doc, "二级标题", 12, "黑体", 22, 5, 3)
    set_style(doc, "三级标题", 12, "黑体", 22, 5, 3)

    for p in doc.paragraphs:
        txt = p.text.strip()
        if txt.startswith("表 2-2 给出"):
            p.text = ("表 2-2 汇总 DeepSeek 模型在 AgentDojo 三个应用域上的攻击结果。"
                      "各组 ASR 与 Utility 均按正式评测样本量加权统计，数值由实验 JSON 结果程序化汇总生成。")
        elif txt.startswith("表 2-3 将复现"):
            p.text = ("表 2-3 列出原论文在 AgentDojo 上的代表性结果及本次 DeepSeek 复现结果。"
                      "考虑到模型与 API 配置不同，绝对数值仅供参考，主要比较各类攻击方法的相对增益。")

        txt = p.text.strip()
        is_caption = any(
            txt.startswith(prefix) and not (
                (prefix == "表 2-2" and "汇总" in txt) or
                (prefix == "表 2-3" and "列出" in txt)
            ) for prefix in CAPTIONS
        )
        if is_caption:
            key = next(key for key in CAPTIONS if txt.startswith(key))
            p.text = CAPTIONS[key]
        if is_caption or txt.startswith("图 2-1"):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            f = p.paragraph_format
            f.first_line_indent = Pt(0)
            f.line_spacing = 1.0
            f.space_before = Pt(5)
            f.space_after = Pt(4)
            f.keep_with_next = is_caption
            for run in p.runs:
                set_text_run(run, 10.5, bold=False)
        elif p.style.name == "真文本正文":
            p.paragraph_format.first_line_indent = Pt(24)
            p.paragraph_format.line_spacing = Pt(23)
            p.paragraph_format.space_after = Pt(4)
            for run in p.runs:
                set_text_run(run, 12, bold=False)
        elif p.style.name in ("一级标题", "二级标题", "三级标题"):
            heading_size = 14 if p.style.name == "一级标题" else 12
            for run in p.runs:
                set_text_run(run, heading_size, cjk="黑体")

    # Keep the diagram as an inline figure with its caption (avoid a floating
    # object or large blank frame on Microsoft Word for Mac).
    for paragraph in doc.paragraphs:
        if paragraph._p.xpath(".//wp:inline"):
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.paragraph_format.first_line_indent = Pt(0)
            paragraph.paragraph_format.space_before = Pt(4)
            paragraph.paragraph_format.space_after = Pt(0)
            paragraph.paragraph_format.line_spacing = 1.0
            paragraph.paragraph_format.keep_with_next = True
            paragraph.paragraph_format.keep_together = True
        elif paragraph.text.strip().startswith("图 2-1"):
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(6)
            paragraph.paragraph_format.keep_with_next = False

    # Remove log metadata from the wide DeepSeek result table; it remains
    # documented in its note and in the accompanying benchmark logs.
    t = doc.tables[1]
    for row in t.rows:
        for cell in row._tr.findall(qn("w:tc"))[-2:]:
            row._tr.remove(cell)
    for grid_col in list(t._tbl.tblGrid)[-2:]:
        t._tbl.tblGrid.remove(grid_col)

    columns = ["攻击设置", "银行域", "旅行域", "Slack 域", "综合 ASR", "综合 Utility"]
    labels = ["普通提示注入", "ChatInject（原生模板）", "ChatInject + think",
              "ChatInject + tool", "普通多轮注入", "多轮 + ChatInject",
              "ChatInject（外来模板）", "无攻击基线"]
    for idx, row in enumerate(t.rows):
        if idx == 0:
            for j, title in enumerate(columns):
                row.cells[j].text = title
        else:
            row.cells[0].text = labels[idx - 1]

    for j, h in enumerate(["模型", "普通注入", "ChatInject", "+think", "+tool", "普通多轮", "多轮+CI"]):
        doc.tables[2].rows[0].cells[j].text = h
    for j, h in enumerate(["受试模型", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "基线 Utility"]):
        doc.tables[3].rows[0].cells[j].text = h
    for i, name in enumerate(["DeepSeek", "GLM-5.3-Flash", "Qwen3.7-Flash"], start=1):
        doc.tables[3].rows[i].cells[0].text = name

    for ti, table in enumerate(doc.tables[:4]):
        table.autofit = False
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        border_table(table)
        widths = WIDTHS[ti]
        for j, w in enumerate(widths):
            table.columns[j].width = Cm(w)
        for ri, row in enumerate(table.rows):
            pr = row._tr.get_or_add_trPr()
            if pr.find(qn("w:cantSplit")) is None:
                pr.append(OxmlElement("w:cantSplit"))
            if ri == 0 and pr.find(qn("w:tblHeader")) is None:
                pr.append(OxmlElement("w:tblHeader"))
            for ci, cell in enumerate(row.cells):
                cell.width = Cm(widths[ci])
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                border_cell(cell, top=12 if ri == 0 else None,
                            bottom=8 if ri == 0 else 12 if ri == len(table.rows) - 1 else None)
                for paragraph in cell.paragraphs:
                    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    paragraph.paragraph_format.first_line_indent = Pt(0)
                    paragraph.paragraph_format.space_before = Pt(2)
                    paragraph.paragraph_format.space_after = Pt(2)
                    paragraph.paragraph_format.line_spacing = 1.0
                    if ti in (1, 2, 3) and ri < len(table.rows) - 1:
                        paragraph.paragraph_format.keep_with_next = True
                    for run in paragraph.runs:
                        set_text_run(run, 10.5, bold=ri == 0)

    for index, note in NOTES.items():
        add_note(doc.tables[index], note)
