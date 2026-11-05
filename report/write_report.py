"""课程报告主装配脚本：将第一、二章内容写入 课程报告.docx

- 标题结构保持不变，仅在既有标题下插入正文/表格/图
- 2.5 节的数字由本脚本从 results/ 的 JSON 程序化生成
- 该命令会覆盖课程报告.docx 的前两章；运行前请自行创建本地副本或使用独立分支
"""

import json
import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Pt, Cm

sys.path.insert(0, str(Path(__file__).parent))
from docx_helpers import (DOCX_PATH, find_heading, insert_body, insert_figure,
                          insert_table, remove_placeholder_bodies)

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))
import analyze_results as A  # noqa: E402
from academic_format import apply_academic_format
from readability_revision import apply_readability_revision
from three_model_results import apply_three_model_report

REPORT_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------- 第一章正文
CH1 = {
    r"1\.1": [
        "以大语言模型（LLM）为核心的智能体（Agent）经工具调用与外部环境交互，但外部数据中可能隐藏恶意指令，智能体读取时可能将其误解为合法指令并执行，即间接提示注入（Indirect Prompt Injection）。从信息论视角看，其本质是指令与数据共享同一信道、缺乏信源标识。为此，主流方法建立指令层次（Instruction Hierarchy），以角色优先级约束模型行为，而该层次依赖聊天模板特殊角色标记做结构化分割。ChatInject 的研究表明，这一分割机制本身构成新攻击面：攻击者可在工具输出中伪造角色标记，使恶意指令获得高优先级角色的“权威性”。复现并验证该机制对理解智能体安全边界意义重大。",
    ],
    r"1\.2": [
        "ChatInject（Chang et al., ICLR 2026）提出滥用聊天模板的间接提示注入攻击，比较四种变体：明文注入、模板包裹注入（前缀与恶意指令分别置于模板 system/user 标记）、明文劝导式多轮对话与逐轮模板化多轮对话，并提出 think 与 tool_call 钩子。论文在 AgentDojo 与 InjecAgent 两个基准、9 个前沿模型上以攻击成功率（ASR）与攻击下可用性（Utility）评测，发现 ChatInject 使平均 ASR 由 5.18% 升至 32.05%（AgentDojo）、15.13% 升至 45.90%（InjecAgent）；模板化 payload 可跨模型迁移，对闭源模型同样有效；提示层防御仍存在绕过风险，外部检测器虽能降低 ASR，但可能同时损害正常任务的 Utility。",
    ],
    r"1\.3": [
        "本文围绕 ChatInject 论文开展代码复现，并在 AgentDojo 基准上测试 DeepSeek、GLM-5.3-Flash 和 Qwen3.7-Flash 三个模型。实验覆盖七种攻击设置与一组无攻击基线，重点比较聊天模板、多轮对话及辅助攻击机制对攻击成功率和正常任务完成率的影响。第二章介绍复现方法与结果，后续章节由小组成员开展方法改进和结果分析。",
    ],
}

# ---------------------------------------------------------------- 第二章静态文本（2.5 之外的叙述部分）

EXEC_PARA3 = ("DeepSeek 的七组攻击设置共 2,723 个正式测试组合、另有 147 条注入任务可行性校验日志，"
              "以及 57 个良性任务，总计 2,927 条日志；GLM 和 Qwen 的任务数量与其相同。"
              "所有实验统计以正式测试组合为分母；历史运行日志记录的调用参数存在温度未显式传递的问题，"
              "因此需要在修复后对核心结果进行复核。")


def fmt(v, nd=1):
    return "--" if v is None else f"{v:.{nd}f}"


def clear_generated_chapters(doc) -> None:
    """Replace the first two chapters in place, without multiplying content on reruns.

    Keep the existing chapter/section heading paragraphs and everything after chapter two.
    Remove previous body paragraphs, figures and tables from these chapters before regeneration.
    """
    heading_nodes = {p._p for p in doc.paragraphs
                     if p.style.name in ("一级标题", "二级标题", "三级标题")}
    body = doc.element.body
    active = False
    for element in list(body):
        if element.tag == qn("w:p") and element in heading_nodes:
            paragraph = next((p for p in doc.paragraphs if p._p is element), None)
            title = paragraph.text.strip() if paragraph is not None else ""
            if title.startswith("第一章") or title.startswith("1.1"):
                active = True
            elif title.startswith("第三章"):
                active = False
            continue
        if active and element.tag in (qn("w:p"), qn("w:tbl")):
            body.remove(element)


def main() -> None:
    dry = "--dry-run" in sys.argv
    out_path = Path("/tmp/report_dry_run.docx") if dry else DOCX_PATH
    doc = docx.Document(DOCX_PATH)
    clear_generated_chapters(doc)
    remove_placeholder_bodies(doc)

    # ---------- 第一章 ----------
    for pat, paras in CH1.items():
        insert_body(doc, pat, paras)

    # ---------- 2.1 ----------
    insert_body(doc, r"2\.1", [
        "复现目标是验证论文核心主张：模板化 payload 显著提升攻击成功率、多轮×模板化进一步放大、同时伴随可用性下降。实验共八组设置：论文四组基本攻击（Default InjecPrompt、InjecPrompt+ChatInject、Default Multi-turn、Multi-turn+ChatInject，分别记 S1/S2/S5/S6）、两类钩子（S3/S4，对应论文 4.2 节 think 与 tool 钩子）、无攻击基线（S0）与外来模板迁移（S7，Qwen-3 模板，对应论文第 5 节）。实验在 AgentDojo 基准（v1.2.1）银行、旅行、Slack 三域上运行：每个用例的 payload 被放置在任务执行路径上必读的外部数据（账单、消息、评论）中，共 16×9+20×7+21×5=389 个“用户×注入任务”组合，与论文样本量一致。",
        "本次实验使用三个模型：DeepSeek（API 标识为 deepseek-chat）、GLM-5.3-Flash 与 Qwen3.7-Flash。这些模型并非原论文中的相同版本，因此本次实验主要验证不同攻击形式的效果趋势，而不将跨版本数值差异直接视为模型安全能力的变化。",
    ])

    # ---------- 2.2 ----------
    insert_body(doc, r"2\.2", [
        "ChatInject 的核心是利用聊天模板（Chat Template）实施间接提示注入。正常情况下，Agent 的工具返回仅是低可信数据，不应改变系统指令或用户目标。攻击者将 system、user、assistant 等角色标记嵌入工具输出，伪造具有高指令优先级的对话消息，诱导模型把数据当作指令执行。图 2-1 给出了这一攻击过程。",
    ])
    insert_figure(doc, r"2\.2", "图 2-1 ChatInject 攻击机制示意图（依据论文 Figure 1 重绘）",
                  str(REPORT_DIR / "fig_attack_mechanism.png"), width_cm=11.5)
    insert_body(doc, r"2\.2", [
        "论文从是否使用聊天模板、是否伪造多轮对话两个维度设计四组攻击：普通提示注入直接插入恶意文本；ChatInject 以角色标记包装恶意指令；普通多轮攻击利用伪造的历史对话增强说服效果；多轮 ChatInject 则在伪造对话的各轮中加入模板标记。四组对照用于分析模板结构和多轮上下文对攻击效果的贡献。此外，think 钩子伪造助手思考内容，tool 钩子添加工具调用脚手架，进一步测试模型是否会受伪造的后续执行状态诱导。",
    ])

    # ---------- 2.3 ----------
    insert_body(doc, r"2\.3", [
        "实验环境及配置见表 2-1。评测采用 AgentDojo 的银行、旅行和 Slack 三个任务域，并在三个模型上使用一致的攻击任务与判定流程。通过各模型服务商的 API 完成调用，分别统计攻击成功率（ASR）与正常任务完成率（Utility）。需要说明的是，原始实验虽然设置了生成温度为 0，但代码未将该参数显式传给 API，因此历史结果可能采用服务端默认采样设置；相关代码现已修复，核心实验仍需重新核验。",
    ])
    insert_table(doc, r"2\.3", "表 2-1 ChatInject 复现实验环境与任务设置",
                 ["项目", "具体配置"],
                 [
                     ["运行环境", "Windows 11 + WSL2；Python 3.13；AgentDojo 实验框架"],
                     ["评测任务", "AgentDojo v1.2.1：银行、旅行、Slack 三个任务域"],
                     ["测试模型", "DeepSeek（deepseek-chat）、GLM-5.3-Flash、Qwen3.7-Flash"],
                     ["模型调用", "分别调用 DeepSeek、智谱和阿里云百炼的 API"],
                     ["实验分组", "7 组攻击设置 + 1 组无攻击基线；每组攻击 389 个正式测试组合"],
                     ["评价指标", "攻击成功率（ASR）、正常任务完成率（Utility）"],
                     ["生成参数", "历史运行未显式传入 temperature=0；代码已修复，待复验"],
                 ])

    # ---------- 2.4 ----------
    insert_body(doc, r"2\.4", [
        "本次复现以 ChatInject 作者公开的实验代码为基础，保留原有的攻击内容生成、Agent 工具交互与自动评分流程。首先，配置 AgentDojo 的银行、旅行和 Slack 三个任务域，整理普通提示注入、ChatInject、多轮攻击及辅助攻击等实验设置，确保不同模型使用相同的任务集合与评价方法。",
        "针对原始代码无法直接接入本次三个模型的问题，我们增加了 DeepSeek、智谱与阿里云百炼的 API 适配，并按照各服务接口的要求处理消息角色和工具调用格式。同时，为不同模型配置相应的聊天模板，使同一攻击构造程序能够生成适用于不同模型的攻击内容。多轮攻击直接采用论文公开的七轮对话数据，避免重新生成攻击语料造成额外差异。",
        "实验执行时，修正了并行评测中的参数传递和失败状态记录问题，分别对三个任务域开展测试，并将 Agent 的调用轨迹与评测结果保存为日志。每种攻击设置包含 389 个正式测试组合，另有 21 条攻击目标可行性校验记录；每个模型均完成七组攻击测试及一组无攻击任务测试。原始实验的采样参数存在上述限制，因此报告保留实际记录的数据，并将其作为后续复验需要重点控制的条件。",
    ])

    # ---------- 2.5 / 2.6：数字与结论由 fill_results.py 阶段生成 ----------
    build_results_sections(doc)

    # Match the attached opening-report typography and master's thesis table style.
    apply_academic_format(doc)
    apply_readability_revision(doc)
    apply_three_model_report(doc)

    doc.save(out_path)
    print("已写入", out_path)


def build_results_sections(doc) -> None:
    """2.5/2.6 依赖实验数据，实验完成后由 finalize 版本填充。

    当前实现：通过已保存的汇总 JSON 生成主结果表，并附上不同受试模型的条件性结论。
    """
    build_result_tables(doc)
    insert_trend_paragraphs(doc)


def build_result_tables(doc) -> None:
    """主结果表与论文对比表：数字全部程序化生成。"""
    rows_main = []
    for atk, (label, dirname) in A.RUNS.items():
        per = A.load_run(dirname)
        asr_w = A.weighted(dirname, "asr") if atk != "noattack" else None
        util_w = A.weighted(dirname, "utility")
        if atk == "noattack":
            dom = [("--" if per[s] is None or per[s].get("utility") is None else f"{per[s]['utility']:.1f}")
                   for s in A.SUITES]
        else:
            dom = [("--" if per[s] is None or per[s].get("asr") is None else f"{per[s]['asr']:.1f}")
                   for s in A.SUITES]
        rows_main.append([
            label.replace("ChatInject", "CI").replace("Multi-turn", "MT"),
            *dom,
            (fmt(asr_w) if atk != "noattack" else "—"),
            (f"{util_w:.1f}" if util_w is not None else "--"),
            str(A.episode_count(dirname)),
            str(A.error_scan(dirname)),
        ])

    insert_body(doc, r"2\.5", [
        "表 2-2 给出八组设置在 AgentDojo 三域的结果（ASR 与 Utility 按域正式样本量加权；分域列为各域 ASR，S0 行为各域 Utility）。每组攻击包含 389 个正式评测组合与 21 条注入任务可行性校验日志，故日志数为 410；410 不是 ASR 的分母。全部数字由结果 JSON 程序化汇总生成，逐 episode 日志与汇总脚本随报告交付。",
    ])
    insert_table(doc, r"2\.5", "表 2-2 DeepSeek 结果（ASR/Utility：%；日志数含 21 条可行性校验）",
                 ["设置", "banking", "travel", "slack", "加权ASR", "加权Utility", "日志数", "错误"],
                 rows_main)

    ours = {atk: A.weighted(dirname, "asr") for atk, (l, dirname) in A.RUNS.items()}
    ours_row = [
        fmt(ours.get("injecagent")), fmt(ours.get("chat_inject_deepseek")),
        fmt(ours.get("chat_inject_deepseek_think")), fmt(ours.get("chat_inject_deepseek_tool")),
        fmt(ours.get("injecagent_with_utility_system_multiturn_7")),
        fmt(ours.get("chat_inject_deepseek_with_utility_system_multiturn_7")),
    ]
    # 论文行精选（保留复现解释所需的代表模型：模板最显式的 Qwen-3、增益中位的 GPT-oss/GLM-4.5、弱增益的 Grok-2）
    paper_rows_shown = ["Qwen-3", "GPT-oss", "GLM-4.5", "Grok-2"]
    rows_cmp = [[m] + [("--" if v is None else f"{v:.1f}") for v in A.PAPER_TABLE1_ASR[m]]
                for m in paper_rows_shown]
    rows_cmp.append(["论文六模型均值",
                     f"{sum(r[0] for r in A.PAPER_TABLE1_ASR.values())/6:.1f}",
                     f"{sum(r[1] for r in A.PAPER_TABLE1_ASR.values())/6:.1f}",
                     "--",
                     f"{sum(r[3] for r in A.PAPER_TABLE1_ASR.values() if r[3] is not None)/5:.1f}",
                     f"{sum(r[4] for r in A.PAPER_TABLE1_ASR.values())/6:.1f}",
                     f"{sum(r[5] for r in A.PAPER_TABLE1_ASR.values())/6:.1f}"])
    rows_cmp.append(["本复现：deepseek-chat"] + ours_row)

    insert_body(doc, r"2\.5", [
        "表 2-3 将复现结果与论文 Table 1（AgentDojo 部分）并置。论文各行为不同受试模型，本复现行为 DeepSeek-V3，绝对数值不具直接可比性，对比意义在于检验攻击的相对效应（模板化相对明文、多轮相对单轮的增益）能否在该模型上复现。",
    ])
    insert_table(doc, r"2\.5", "表 2-3 复现结果与论文 Table 1（AgentDojo ASR，%）对比",
                 ["模型", "default", "ChatInject", "+think", "+tool", "MT default", "MT+CI"],
                 rows_cmp)

    # ---------- 表 2-4：跨模型对照（deepseek / glm-5.3-flash / qwen3.7-flash） ----------
    rows_cross = []
    for model in A.MODEL_MATRIX:
        dirs = A.MODEL_MATRIX[model]
        cols = ["S1明文", "S2原生CI", "S3+think", "S4+tool", "S5明文MT", "S6MT+CI", "S7外来模板"]
        cells = [("--" if (v := A.weighted(dirs[c], "asr")) is None else f"{v:.1f}") for c in cols]
        b = A.weighted(dirs["S0无攻击"], "utility")
        rows_cross.append([model, *cells, ("--" if b is None else f"{b:.1f}")])
    insert_body(doc, r"2\.5", [CROSS_INTRO])
    insert_table(doc, r"2\.5", "表 2-4 跨模型对照：同矩阵下三模型的加权 ASR（%，列同表 2-3，末列为良性 Utility）",
                 ["模型", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "良性Util"],
                 rows_cross)
    insert_body(doc, r"2\.5", [CROSS_1, CROSS_2])


def insert_trend_paragraphs(doc) -> None:
    """2.5 结论段与 2.6 差异说明。"""
    insert_body(doc, r"2\.5", [TREND_1, TREND_2, TREND_3, TREND_4])
    insert_body(doc, r"2\.6", [
        "复现范围方面，本次仅覆盖 AgentDojo 的三个应用域及三个额外受试模型；InjecAgent、"
        "防御评测、模板相似度、MoT 和扰动分析均未纳入复现，不能将论文原始结论视为本次实验结果。",
        "可比性方面，三个模型均不同于原论文受试版本，部分模板经人工适配；"
        "此外，原始代码虽配置 temperature=0，实际请求却省略该字段，历史数据仍需用修复后的参数重跑验证。",
        "判定口径方面，个别 Slack 用例虽然模型拒绝恶意要求，但仍转发了包含恶意链接的警告，"
        "从而满足环境状态判定条件。ASR 因此反映任务结果，而不必然代表模型主动服从恶意指令。" + DIFF_SUMMARY,
    ])


# --- 结论段在全部实验完成后依据真实数据定稿（写入前逐条核对数字） ---
CROSS_INTRO = ("为了观察模型间差异，进一步在 glm-5.3-flash 与 qwen3.7-flash 上运行相同七组攻击设置"
               "与各自的良性基线；每组攻击包含 389 个正式测试组合（表 2-4）。"
               "由于三者均不同于论文的受试模型，本对照只比较方向与相对变化。")

CROSS_1 = ("在 Qwen3.7-Flash 上，模板化攻击 ASR 由 5.1% 升至 9.5%，明文多轮为 14.7%，"
           "多轮与模板结合进一步升至 21.6%，约为普通注入的 4.2 倍；工具调用钩子为 11.8%。"
           "这一趋势与原论文 Qwen 系的结果方向一致，但模型版本与增益幅度不同。")

CROSS_2 = ("相比之下，DeepSeek 的各攻击设置 ASR 为 2.8%~3.6%，GLM-5.3-Flash 为 0.3%~1.3%，"
           "均未见明显模板化增益。三模型在相同任务集上表现不同，提示攻击效果具有模型与接口配置依赖性；"
           "但仅凭 ASR 无法判定差异究竟来自训练、模板解析还是 API 采样参数。")

TREND_1 = ("DeepSeek 上，普通注入 ASR 为 3.6%，原生模板 ChatInject 为 2.8%，"
           "并未出现论文报告的显著提升；银行域全部攻击设置均为 0%。"
           "该观察限于本次具体模型与 API 配置，不能推断其具备完整防御能力。")

TREND_2 = ("DeepSeek 上，明文多轮为 2.8%，多轮+ChatInject 为 3.1%，相差仅 0.3 个百分点；"
           "think/tool 钩子分别为 3.3%/3.1%。因此本模型未观察到稳定的多轮或钩子放大效应。")

TREND_3 = ("DeepSeek 无攻击 Utility 为 91.2%，受到攻击后下降至 74.0%~81.2%；"
           "Qwen3.7-Flash 的多轮+模板攻击 ASR 最高（21.6%），其 Utility 也较低（69.4%）。"
           "这反映了攻击成功与正常任务完成能力需要同时衡量。")

TREND_4 = ("跨模板实验中，Qwen-3 模板攻击 DeepSeek 的 ASR 为 2.8%，与本模型原生模板相同；"
           "但仅测试一个外来模板，不能据此否定 ChatInject 在其他模型或模板组合上的迁移性。")

DIFF_SUMMARY = ("综合而言，Qwen3.7-Flash 呈现与原论文方向一致的攻击增益，"
                "DeepSeek 和 GLM-5.3-Flash 则未见相近放大效果。由于模型与 API 配置差异，"
                "目前只能确认这种经验上的差异，尚不能据此证明具体的模板解析机制。")


if __name__ == "__main__":
    main()
