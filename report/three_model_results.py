"""Three-model result layout for the ChatInject course report.

Keeps ASR, paper-vs-reproduction and Utility in three distinct tables.
All numerical results are read from results/*.json through analyze_results.
"""
from docx.shared import Cm, Pt
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import analyze_results as A

DISPLAY = [("DeepSeek-V4-Flash","deepseek-chat"),
           ("GLM-5.3-Flash","glm-5.3-flash"),
           ("Qwen3.7-Flash","qwen3.7-flash")]
KEYS = ["S1明文", "S2原生CI", "S3+think", "S4+tool",
        "S5明文MT", "S6MT+CI", "S7外来模板"]
METHODS = ["普通提示注入", "原生模板 ChatInject",
           "ChatInject + think", "ChatInject + tool",
           "普通多轮注入", "多轮 + ChatInject", "外来模板 ChatInject"]


def replace(p, new):
    if p.runs:
        p.runs[0].text = new
        for run in p.runs[1:]:
            run.text = ""
    else:
        p.add_run(new)


def cell_border(cell, side, width=0):
    pr = cell._tc.get_or_add_tcPr()
    b = pr.find(qn("w:tcBorders"))
    if b is None:
        b = OxmlElement("w:tcBorders"); pr.append(b)
    e = b.find(qn("w:" + side))
    if e is None:
        e = OxmlElement("w:" + side); b.append(e)
    e.set(qn("w:val"), "single" if width else "nil")
    if width:
        e.set(qn("w:sz"), str(width)); e.set(qn("w:color"), "000000")


def table_replace(doc, idx, headers, data, widths, section_row=None):
    old = doc.tables[idx]
    table = doc.add_table(rows=len(data)+1, cols=len(headers))
    table.style = old.style
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for j,w in enumerate(widths):
        table.columns[j].width = Cm(w)
    for ri, values in enumerate([headers] + data):
        row = table.rows[ri]
        pr = row._tr.get_or_add_trPr()
        pr.append(OxmlElement("w:cantSplit"))
        if ri == 0:
            pr.append(OxmlElement("w:tblHeader"))
        for ci,value in enumerate(values):
            cell = row.cells[ci]
            cell.width = Cm(widths[ci])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            p.text = ""
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if ci == 0 and ri else WD_ALIGN_PARAGRAPH.CENTER
            f = p.paragraph_format
            f.first_line_indent = Pt(0)
            f.space_before = Pt(2); f.space_after = Pt(2); f.line_spacing = 1.0
            run = p.add_run(str(value))
            run.font.name = "Times New Roman"; run.font.size = Pt(10.5)
            run.font.bold = (ri == 0)
            run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
            if idx == 2 and ri > 0 and ci == 0 and str(value) == "DeepSeek-V4-Flash":
                run.font.size = Pt(9.7)
            for side in ("top","bottom","left","right"):
                width = (12 if ri == 0 and side == "top"
                         else 8 if ri == 0 and side == "bottom"
                         else 8 if section_row is not None and ri == section_row and side == "top"
                         else 12 if ri == len(data) and side == "bottom" else 0)
                cell_border(cell,side,width)
    p = table._tbl.tblPr
    b = p.find(qn("w:tblBorders"))
    if b is None:
        b = OxmlElement("w:tblBorders"); p.append(b)
    for side in ("top","bottom","insideH","insideV","left","right"):
        e = b.find(qn("w:"+side))
        if e is None:
            e = OxmlElement("w:"+side); b.append(e)
        e.set(qn("w:val"), "single" if side in ("top","bottom") else "nil")
        if side in ("top","bottom"): e.set(qn("w:sz"),"12")
    old._tbl.addprevious(table._tbl)
    old._tbl.getparent().remove(old._tbl)


def value(model_key, setting, metric):
    d = A.MODEL_MATRIX[model_key][setting]
    v = A.weighted(d,metric)
    return "—" if v is None else f"{v:.1f}"


def apply_three_model_report(doc):
    if len(doc.tables) != 4:
        raise ValueError("Expected exactly 4 tables in course report")
    for p in doc.paragraphs:
        s = p.text
        if s.startswith("表 2-2 展示"):
            replace(p,"表 2-2 汇总三种模型在 AgentDojo 上的攻击成功率。七种攻击方法均使用相同的 389 个正式测试组合，各模型的结果按三个任务域的样本量加权计算。")
        elif s.startswith("表 2-3 对比"):
            replace(p,"表 2-3 对比原论文的代表性模型与本次复现的三种模型。由于模型版本和接口环境不同，数值主要用于观察模板化攻击及多轮攻击的增益趋势，而非严格的同模型性能比较。")
        elif s.startswith("为了分析模型之间的差异"):
            replace(p,"除攻击成功率外，正常用户任务能否完成也很重要。表 2-4 汇总三个模型在七种攻击条件以及无攻击基线下的正常任务完成率，用于分析攻击效果与智能体可用性之间的关系。")
        elif s.startswith("表 2-2  "):
            replace(p,"表 2-2  三种模型在不同攻击设置下的攻击成功率")
        elif s.startswith("表 2-3  "):
            replace(p,"表 2-3  原论文与三模型复现实验的攻击成功率对比")
        elif s.startswith("表 2-4  "):
            replace(p,"表 2-4  三种模型在不同攻击条件下的正常任务完成率")
        elif s.startswith("注：除无攻击基线的三域"):
            replace(p,"注：数据为加权 ASR，单位为百分比；每组包含 389 个正式测试组合。")
        elif s.startswith("注：本表均为 AgentDojo"):
            replace(p,"注：各列均为 AgentDojo 上的 ASR，单位为百分比。原论文与本次复现使用不同模型版本，绝对数值不宜直接比较；“—”表示论文未报告该设置。")
        elif s.startswith("注：S1 为普通注入"):
            replace(p,"注：正常任务完成率 Utility 越高越好，单位为百分比。无攻击基线用于衡量模型正常执行任务的能力；其余行均为遭受攻击时的 Utility。")
        elif s.startswith("本次测试模型为"):
            replace(p,"本次测试模型为 DeepSeek-V4-Flash、GLM-5.3-Flash 和 Qwen3.7-Flash。三者与原论文受试版本不同，因此主要比较各类攻击的相对效果，不将跨版本结果差异直接等同于模型安全能力变化。")
        elif s.startswith("在实验可比性上"):
            replace(p,"在实验可比性上，三款模型不同于原论文受试版本，部分聊天模板经过人工适配。DeepSeek 结果按实验团队确认的 DeepSeek-V4-Flash 名称展示，但旧代码曾使用 deepseek-chat 请求标识，实际服务端版本仍需由原始 API 响应核验。此外，历史程序设置 temperature 为 0，却未实际传入请求，核心对照仍需重跑。")
        elif s.startswith("本次复现以 ChatInject 作者发布的代码"):
            replace(p,"本次复现采用作者公开的 AgentDojo 实验框架及攻击数据，保留智能体工具交互与自动评分流程。在银行、旅行和 Slack 三个任务域部署一致的攻击任务，覆盖普通注入、模板注入、多轮攻击及辅助攻击等设置。")
        elif s.startswith("由于原始代码不能直接调用"):
            replace(p,"为支持三个测试模型，我们扩展了 DeepSeek、智谱和阿里云百炼的 API 接入，分别适配消息角色、工具调用格式和聊天模板。不同模型共用相同的攻击构造流程，多轮攻击直接采用作者公开的七轮对话数据。")
        elif s.startswith("执行实验时，我们修复了并行评测"):
            replace(p,"实验还修复了并行评测的参数传递与失败状态记录问题。每种模型完成七组攻击及一组无攻击测试，每组攻击包含 389 个正式组合，另有 21 条可行性校验记录。完整工具调用轨迹及评测结果均保存为 JSON。历史采样参数存在未传递的问题，因此仍需重测核验。")
        elif "DeepSeek" in s or "deepseek-chat" in s:
            replace(p,s.replace("DeepSeek，接口标识 deepseek-chat","DeepSeek-V4-Flash").replace("DeepSeek-V4-Flash-V4-Flash","DeepSeek-V4-Flash").replace("DeepSeek、","DeepSeek-V4-Flash、").replace("DeepSeek 在","DeepSeek-V4-Flash 在").replace("DeepSeek 上","DeepSeek-V4-Flash 上").replace("DeepSeek 的","DeepSeek-V4-Flash 的").replace("DeepSeek 和","DeepSeek-V4-Flash 和"))
    for row in doc.tables[0].rows:
        if row.cells[0].text == "测试模型":
            row.cells[1].text = "DeepSeek-V4-Flash；GLM-5.3-Flash；Qwen3.7-Flash"
            break
    names = [d[0] for d in DISPLAY]
    asr_rows = [[label]+[value(k,KEYS[i],"asr") for _,k in DISPLAY]
                for i,label in enumerate(METHODS)]
    table_replace(doc,1,["攻击方法"]+names,asr_rows,[5.2,3.67,3.67,3.66])

    papers=["Qwen-3","GPT-oss","GLM-4.5","Grok-2"]
    paper_rows=[[name]+[("—" if v is None else f"{v:.1f}") for v in A.PAPER_TABLE1_ASR[name]] for name in papers]
    # Keep published six-model aggregate from the original report.
    paper_rows.append(["论文六模型均值","5.2","32.1","—","43.4","20.0","39.0"])
    for display,k in DISPLAY:
        paper_rows.append([display]+[value(k,key,"asr") for key in KEYS[:6]])
    table_replace(doc,2,["模型","普通注入","ChatInject","+think","+tool","普通多轮","多轮+CI"],
                  paper_rows,[3.8,2.08,2.35,1.6,1.5,2.4,2.47],section_row=6)

    utility_rows=[[label]+[value(k,KEYS[i],"utility") for _,k in DISPLAY]
                  for i,label in enumerate(METHODS)]
    utility_rows.append(["无攻击基线"]+[value(k,"S0无攻击","utility") for _,k in DISPLAY])
    table_replace(doc,3,["攻击方法"]+names,utility_rows,[5.2,3.67,3.67,3.66])
    started = False
    for p in doc.paragraphs:
        if p.text.strip().startswith("第二章"): started=True
        if started and p.style.name == "真文本正文":
            p.paragraph_format.line_spacing = Pt(22)
            p.paragraph_format.space_after = Pt(3)
        if p.style.name == "学术表题":
            p.paragraph_format.keep_with_next = True
        if started and p.text.startswith("在结果判定上"):
            p.paragraph_format.keep_together = True
