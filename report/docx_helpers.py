"""课程报告.docx 内容写入工具

保持文档既有标题结构与样式：在指定二级标题后插入正文段落（真文本正文样式）、
表格（算法/表格样式 + 三线表边框）与图片（居中 + 题注）。

用法：作为库被 write_report.py 调用；独立运行时对副本做插入自检。
"""

import copy
import re
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCX_PATH = PROJECT_ROOT / "课程报告.docx"


def find_heading(doc: docx.Document, pattern: str):
    """按正则匹配标题段落（样式须为 一级标题/二级标题/三级标题）。"""
    rx = re.compile(pattern)
    for p in doc.paragraphs:
        if p.style.name in ("一级标题", "二级标题", "三级标题") and rx.search(p.text):
            return p
    raise ValueError(f"heading not found: {pattern}")


HEADING_STYLE_IDS = None  # 延迟初始化：{style_id: name}


def _heading_ids(doc: docx.Document) -> set:
    """一级/二级/三级标题样式的 styleId 集合。"""
    global HEADING_STYLE_IDS
    if HEADING_STYLE_IDS is None:
        ids = set()
        for s in doc.styles:
            if s.name in ("一级标题", "二级标题", "三级标题"):
                ids.add(s.style_id)
        HEADING_STYLE_IDS = ids
    return HEADING_STYLE_IDS


def _anchor_element(doc: docx.Document, heading_paragraph, after_body: bool):
    """返回插入锚点元素：after_body=False 时为标题本身；否则为标题与下一标题之间
    的最后一个元素（段落或表格——doc.paragraphs 不含表格，必须按 body 元素序遍历，
    否则后插的表格会错位到先前内容之前）。"""
    if not after_body:
        return heading_paragraph._p
    heading_el = heading_paragraph._p
    started = False
    last = None
    for el in doc.element.body.iterchildren():
        if el is heading_el:
            started = True
            continue
        if not started:
            continue
        if el.tag == qn("w:p"):
            pPr = el.find(qn("w:pPr"))
            if pPr is not None:
                pStyle = pPr.find(qn("w:pStyle"))
                if pStyle is not None and pStyle.get(qn("w:val")) in _heading_ids(doc):
                    break
            last = el
        elif el.tag == qn("w:tbl"):
            last = el
    return last if last is not None else heading_el


def _new_body_paragraph(doc: docx.Document, after_el):
    """在 after_el（w:p 或 w:tbl 元素，或 Paragraph）之后创建真文本正文段落。"""
    from docx.text.paragraph import Paragraph

    if hasattr(after_el, "_p"):
        after_el = after_el._p
    template = None
    for p in doc.paragraphs:
        if p.style.name == "真文本正文" and p.text.strip():
            template = p
            break
    if template is not None:
        new_p = copy.deepcopy(template._p)
        for r in new_p.findall(qn("w:r")):
            new_p.remove(r)
    else:
        style = doc.styles["真文本正文"]
        new_p = doc.element.makeelement(qn("w:p"), {})
        pPr = new_p.makeelement(qn("w:pPr"), {})
        pStyle = pPr.makeelement(qn("w:pStyle"), {qn("w:val"): style.style_id})
        pPr.append(pStyle)
        new_p.append(pPr)
    after_el.addnext(new_p)
    return Paragraph(new_p, doc)


def insert_body(doc: docx.Document, heading_pattern: str, paragraphs: list[str]) -> None:
    """在该标题节末尾（下一标题前）依序追加若干正文段落。"""
    anchor = _anchor_element(doc, find_heading(doc, heading_pattern), after_body=True)
    for text in paragraphs:
        p = _new_body_paragraph(doc, anchor)
        run = p.add_run(text)
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
        anchor = p


def _set_cell_text(cell, text: str, bold: bool = False, align="center") -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = {"center": WD_ALIGN_PARAGRAPH.CENTER, "left": WD_ALIGN_PARAGRAPH.LEFT}[align]
    run = p.add_run(text)
    run.font.bold = bold
    run.font.size = Pt(9)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")


def _three_line_borders(table) -> None:
    """给表格加三线表边框（顶线、底线、表头下线）。"""
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = tblPr.find(qn("w:tblBorders"))
    if borders is None:
        borders = tblPr.makeelement(qn("w:tblBorders"), {})
        tblPr.append(borders)
    for tag, sz in (("top", "12"), ("bottom", "12")):
        el = borders.find(qn(f"w:{tag}"))
        if el is None:
            el = borders.makeelement(qn(f"w:{tag}"), {})
            borders.append(el)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:color"), "000000")
    # 表头下线通过首行单元格底边框实现
    for cell in table.rows[0].cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tcB = tcPr.find(qn("w:tcBorders"))
        if tcB is None:
            tcB = tcPr.makeelement(qn("w:tcBorders"), {})
            tcPr.append(tcB)
        b = tcB.makeelement(qn("w:bottom"), {})
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "6")
        b.set(qn("w:color"), "000000")
        tcB.append(b)


def insert_table(doc: docx.Document, heading_pattern: str, caption: str, header: list[str],
                 rows: list[list[str]], after_body: bool = True) -> None:
    """在标题（或标题后最后一段正文/表格）后插入题注 + 三线表。"""
    anchor = _anchor_element(doc, find_heading(doc, heading_pattern), after_body)

    # 题注段落
    cap_p = _new_body_paragraph(doc, anchor)
    cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_p.paragraph_format.first_line_indent = Cm(0)
    run = cap_p.add_run(caption)
    run.font.size = Pt(9)
    run.font.bold = True
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")

    table = doc.add_table(rows=len(rows) + 1, cols=len(header))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j, h in enumerate(header):
        _set_cell_text(table.rows[0].cells[j], h, bold=True)
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            align = "left" if (j == 0 and len(str(v)) > 12) else "center"
            _set_cell_text(table.rows[i + 1].cells[j], str(v), align=align)
    _three_line_borders(table)
    # 把表格 XML 移动到题注之后
    cap_p._p.addnext(table._tbl)


def insert_figure(doc: docx.Document, heading_pattern: str, caption: str, img_path: str,
                  width_cm: float = 13.5, after_body: bool = True) -> None:
    """在标题（或其后正文/表格）后插入图片 + 题注。"""
    anchor = _anchor_element(doc, find_heading(doc, heading_pattern), after_body)

    img_p = _new_body_paragraph(doc, anchor)
    img_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    img_p.paragraph_format.first_line_indent = Cm(0)
    img_p.add_run().add_picture(img_path, width=Cm(width_cm))

    cap_p = _new_body_paragraph(doc, img_p)
    cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap_p.paragraph_format.first_line_indent = Cm(0)
    run = cap_p.add_run(caption)
    run.font.size = Pt(9)
    run.font.bold = True
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")


def remove_placeholder_bodies(doc: docx.Document) -> None:
    """删除文档中空的真文本正文占位段。"""
    for p in list(doc.paragraphs):
        if p.style.name == "真文本正文" and not p.text.strip():
            p._p.getparent().remove(p._p)


if __name__ == "__main__":
    # 自检：在副本上插入样例内容
    import shutil

    test_path = "/tmp/report_insert_test.docx"
    shutil.copy(DOCX_PATH, test_path)
    d = docx.Document(test_path)
    remove_placeholder_bodies(d)
    insert_body(d, r"1\.1", ["测试段落一：本段用于验证样式与缩进是否正确继承。", "测试段落二。"])
    insert_table(d, r"1\.1", "表 1-1 测试表格", ["列A", "列B"], [["a", "1"], ["b", "2"]])
    insert_figure(d, r"1\.2", "图 1-1 测试图", "test_fig.png", width_cm=10) if Path("test_fig.png").exists() else None
    d.save(test_path)
    d2 = docx.Document(test_path)
    print("自检通过，段落数:", len(d2.paragraphs), "表格数:", len(d2.tables))
    for p in d2.paragraphs[:8]:
        print(f"[{p.style.name}] {p.text[:40]}")
