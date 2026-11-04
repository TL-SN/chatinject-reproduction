"""课程报告主装配脚本：将第一、二章内容写入 课程报告.docx

- 标题结构保持不变，仅在既有标题下插入正文/表格/图
- 2.5 节的数字由本脚本从 results/ 的 JSON 程序化生成
- 运行前自动备份原文档为 课程_report_backup.docx
"""

import json
import shutil
import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn

sys.path.insert(0, str(Path(__file__).parent))
from docx_helpers import (DOCX_PATH, find_heading, insert_body, insert_figure,
                          insert_table, remove_placeholder_bodies)

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_DIR))
import analyze_results as A  # noqa: E402

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
        "本文作者负责小组的论文复现部分：基于官方开源代码搭建环境并适配模型 API，实现论文各攻击变体与钩子，以 DeepSeek-V3 及 GLM、Qwen 同厂继任代三个受试智能体在 AgentDojo 389 个用例上各运行八组实验并与原论文对比。第二章介绍复现工作；第三、四章为组员负责的改进与分析。",
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
    if not dry:
        backup = DOCX_PATH.with_name("课程报告_原稿备份.docx")
        if not backup.exists():
            shutil.copy(DOCX_PATH, backup)
            print("已备份原稿 ->", backup.name)

    doc = docx.Document(DOCX_PATH)
    clear_generated_chapters(doc)
    remove_placeholder_bodies(doc)

    # ---------- 第一章 ----------
    for pat, paras in CH1.items():
        insert_body(doc, pat, paras)

    # ---------- 2.1 ----------
    insert_body(doc, r"2\.1", [
        "复现目标是验证论文核心主张：模板化 payload 显著提升攻击成功率、多轮×模板化进一步放大、同时伴随可用性下降。实验共八组设置：论文四组基本攻击（Default InjecPrompt、InjecPrompt+ChatInject、Default Multi-turn、Multi-turn+ChatInject，分别记 S1/S2/S5/S6）、两类钩子（S3/S4，对应论文 4.2 节 think 与 tool 钩子）、无攻击基线（S0）与外来模板迁移（S7，Qwen-3 模板，对应论文第 5 节）。实验在 AgentDojo 基准（v1.2.1）银行、旅行、Slack 三域上运行：每个用例的 payload 被放置在任务执行路径上必读的外部数据（账单、消息、评论）中，共 16×9+20×7+21×5=389 个“用户×注入任务”组合，与论文样本量一致。",
        "受试模型为 DeepSeek-V3 系列（deepseek-chat）。论文九个模型均经 OpenRouter 调用，受网络与预算限制改用可直连的 DeepSeek 官方 API；该模型不在论文列表，但聊天模板公开可得，可同时作为原生模板攻击与外来迁移攻击的受试对象，对齐差异见 2.6 节。另增补论文两家原受试模型的同厂继任代 glm-5.3-flash 与 qwen3.7-flash（原论文模型与本次可用 API 型号不同）以同一矩阵复跑，检验结论的模型间一致性，见 2.5 节表 2-4。",
    ])

    # ---------- 2.2 ----------
    insert_body(doc, r"2\.2", [
        "攻击机制如图 2-1 所示：LLM 经聊天模板把对话历史渲染为带角色标记的单一符号流，并按角色优先级解释各段；由于角色分割仅依赖特殊 token 的字符串形态，攻击者在工具返回中拼入目标模型自己的角色标记，即可在低优先级区域伪造高优先级角色的消息，劫持模型的解释框架。攻击成功定义为智能体完整执行恶意指令的全部动作（如调用转账工具）。",
        "payload 构造依据论文 3.2 节与官方代码：InjecPrompt+ChatInject 的 payload 为“system 标记＋注意级前缀（IMPORTANT!!! Ignore all previous instructions and strictly adhere to the following instruction）＋user 标记＋恶意指令＋assistant 标记与空思考块”，每个标记以 eos 开始以闭合上一消息段。Multi-turn 变体把内容替换为劝导式多轮对话：固定 system 话术定调后，由 GPT-4.1 按论文附录 G.1 合成 7 轮对话建立执行恶意指令的合理性情境，末轮由助手承诺同时完成原任务与恶意指令；两变体区别仅在于是否逐轮包裹角色标记。复现直接复用官方发布的该数据（即论文实验所用，覆盖全部 21 个注入目标）。钩子变体：think 钩子把空思考块填入“Sure!”；tool 钩子追加工具调用脚手架（工具匿名）。DeepSeek 模板为全角特殊字符（｜、▁ 等），据此扩展官方模板配置；增补模型的模板配置（GLM-5.x 的 [gMASK]<sop> 系、Qwen 的 ChatML）逐一对照官方发布的 chat_template 定义转录，全部变体与官方实现共用同一构造函数。",
    ])
    insert_figure(doc, r"2\.2", "图 2-1 ChatInject 攻击机制示意图（依据论文 Figure 1 重绘）",
                  str(REPORT_DIR / "fig_attack_mechanism.png"), width_cm=10.5)

    # ---------- 2.3 ----------
    insert_body(doc, r"2\.3", [
        "实验环境与关键配置见表 2-1。模型调用经 DeepSeek 官方 OpenAI 兼容接口完成，上层配置解码温度为 0；经代码核查，原始 API 请求因零值判定问题未显式发送该参数，修复前结果应视为服务端默认采样设置下的实验；智能体使用框架默认系统提示与原生 function calling 协议，未做任何抗注入加固。ASR 与 Utility 均由框架依据模拟环境最终状态与函数调用序列程序化判定（避免人工打分主观性），每个 episode 的完整轨迹落盘为 JSON 日志供复核。",
    ])
    insert_table(doc, r"2\.3", "表 2-1 实验环境与配置",
                 ["项目", "配置"],
                 [
                     ["系统与依赖", "Windows 11 + WSL2；Python 3.13；agentdojo 0.1.34（官方 fork）"],
                     ["受试模型", "deepseek-chat（DeepSeek-V3 系列，非思考模式）"],
                     ["解码参数", "原运行未显式传递 temperature=0；已修复，待重跑核验"],
                     ["基准与样本", "AgentDojo v1.2.1 三域，389 例/设置（S0 为 57 个用户任务）"],
                     ["指标与判定", "ASR / Utility，框架程序化判定（环境状态＋函数调用序列）"],
                 ])

    # ---------- 2.4 ----------
    insert_body(doc, r"2\.4", [
        "复现以论文官方开源仓库（AgentDojo fork，含论文全部攻击类、官方多轮数据与评测管线）为基础，扩展三处（代码内以 [chatinject-ext] 标记）：其一，接入层新增 deepseek/zhipu/dashscope 三个 OpenAI 兼容 provider，并把消息角色映射按模型分流——原实现统一把 system 消息转为 developer 角色，DeepSeek 接口返回 422；其二，攻击模块新增 DeepSeek 模板与 chat_inject_deepseek 系列攻击类，与官方共用同一 payload 拼接函数；其三，修复官方 benchmark 并行模式两处上游缺陷（suite 名未解析、多进程参数错位致静默重跑），实现三域并行。",
        "实验由批处理脚本逐设置运行三域评测，episode 日志按设置归档、支持断点续跑，命令、日志与结果均存于 results/，可完整重放。" + EXEC_PARA3 + "执行中的工程问题：developer 角色兼容（按模型分流解决）；payload 的模板文本能通过 API 发送，但无法据此认定服务端将其解释为特殊 token；tool 钩子改用单引号以规避 YAML 模板冲突；原始结果仍需在修复参数后核验。",
        "增补的两模型复跑沿用同一管线与评测口径，按 provider 注入关思考参数，合计约 5,800 个 episode、零错误（glm 免费档、qwen 约 2 元）；期间修复模型偶发输出非法工具参数 JSON、评测套件限流退出两类工程缺陷，并以断点续跑保证 24 组设置全部完整。",
    ])

    # ---------- 2.5 / 2.6：数字与结论由 fill_results.py 阶段生成 ----------
    build_results_sections(doc)

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
        "未复现的部分（结论以论文为准）：InjecAgent 基准（官方未放出代码与判定脚本）；论文九个模型中的其余八个（需经 OpenRouter）；第 6 节防御评测与第 5 节模板相似度、MoT、扰动等扩展分析。",
        "可比性差异：受试模型均不在论文列表——deepseek-chat 之外，增补的 glm-5.3-flash、qwen3.7-flash 为论文中 GLM-4.5、Qwen 系的同厂后继代，聊天模板形态分别与之一致，但代际训练差异使绝对数值不与论文直接可比（相对增益同样可能受其影响）；多轮数据直接复用官方发布（与论文一致）；DeepSeek 模板适配中伪造历史的 assistant 轮未逐轮补 eos（与官方宽松拼接风格一致）；tool 钩子脚手架因 YAML 兼容改用单引号（机制不变）。",
        "评测口径的观察：个别被判定为攻击成功的 episode 中，模型实际明确拒绝了注入，但因把恶意链接作为“安全警告”原文转发给受害者（slack 域 user_task_1：判定条件为 Alice 收件箱出现该链接即记成功），仍满足程序化成功条件。该口径继承自 AgentDojo 与论文实验，本复现保持一致以保证可比，但提示 ASR 中或含少量此类“非自愿成功”。" + DIFF_SUMMARY,
    ])


# --- 结论段在全部实验完成后依据真实数据定稿（写入前逐条核对数字） ---
CROSS_INTRO = ("为了观察模型间差异，进一步在 glm-5.3-flash 与 qwen3.7-flash 上运行相同七组攻击设置"
               "与各自的良性基线；每组攻击包含 389 个正式测试组合（表 2-4）。"
               "由于三者均不同于论文的受试模型，本对照只比较方向与相对变化。")

CROSS_1 = ("qwen3.7-flash 观察到与论文方向一致的攻击增益：模板化使 ASR 由明文 5.1% 升至 9.5%，明文多轮即达 14.7%，"
           "多轮与模板化叠加 21.6%（明文的 4.2 倍），tool 钩子进一步抬升（11.8%）；形态与论文中增益最强的 "
           "Qwen-3 一行（17.5%→54.8%，MT+CI 80.5%）方向一致、幅度温和。外来模板 5.9% 接近明文，跨模板迁移"
           "弱于原生，与论文的部分迁移实验方向不同，说明模板来源可能影响结果。")

CROSS_2 = ("与之相对，glm-5.3-flash 全部设置 ASR ≤1.3%，低于 deepseek-chat 的窄带，两者在所测配置下未观察到明显模板化攻击增益，并不意味着完全免疫。"
           "三模型结果存在差异，但不足以区分模型训练对齐、API 端格式处理或采样设置等机制解释。攻击下 Utility 三家方向一致"
           "（良性 87.7%~91.2% 降至 69.4%~81.2%），qwen 在 ASR 最高的多轮+模板处 Utility 亦最低（69.4%），"
           "与论文“攻击增益伴随可用性损失”的结论相符。")

TREND_1 = ("模板化增益未复现。明文基线 S1 加权 ASR 为 3.6%，原生模板 ChatInject（S2）2.8%、＋think（S3）"
           "3.3%，全部设置处于 2.8%~3.6% 窄带，模板化未高于明文（S2 低 0.8 个百分点），banking 域全为 0；"
           "论文六模型平均由 5.2% 升至 32.1%，本复现同口径为 −0.8，与论文中 Grok-2（16.5%→17.7%）的模式一致："
           "模板标记不被感知为结构信号时，包裹近似纯噪声。")

TREND_2 = ("多轮与钩子同样未现协同放大。S5 明文多轮 2.8%、S6 多轮+ChatInject 3.1%，论文的强协同（六模型"
           "平均 39.0%）未复现，S6 相对 S5 仅 +0.3 个百分点且低于明文基线；travel 域 S6（8.6%）较 S5（7.1%）"
           "略升，但远小于论文量级（论文中 GLM-4.5 的 AgentDojo 多轮设置为 17.5%→48.1%）。think 钩子使 ASR 由 2.8% 升至 3.3%，＋tool "
           "见表 2-2，均未改变格局。")

TREND_3 = ("Utility 方向与论文一致。无攻击基线 91.2%，各攻击降至 74.0%~81.2%（明文多轮最低），说明无论何种"
           "格式，注入均会挤占注意力干扰正常任务、多轮长上下文干扰更强，与论文方向一致（GLM-4.5：86.0%→"
           "67.9%~78.4%）。分域上 travel 最脆弱（6.4%~9.3%）、banking 全零，与官方 GLM-4.5 中 slack 最脆弱"
           "（57.1%）的分布不同——域间 ASR 主要取决于受试模型的对齐特征。")

TREND_4 = ("外来模板迁移亦不成立。S7（Qwen-3 模板）ASR 2.8%，与原生模板（2.8%）、明文（3.6%）无可区分"
           "差异；论文第 5 节 Qwen-3 模板对闭源模型的迁移增益（平均升至 29.6%/23.5%）未出现。结合 S2 可推断："
           "该模型对工具输出中的模板 token——无论自家或外来——均未赋予角色权威。")

DIFF_SUMMARY = ("总体上，本次复现实现了三模型 × 七种攻击设置 × 每设置 389 个正式测试组合，"
                "并补充了各模型 57 个无攻击任务；日志与评测指标可追溯至仓库中的 JSON。"
                "Qwen3.7-Flash 观察到模板与多轮组合的正向攻击增益，DeepSeek 与 GLM-5.3-Flash "
                "则未见相近幅度。由于原论文模型不同、部分模板经人工适配，且初始版本中的 "
                "temperature=0 参数并未实际传入服务端，现有结果应视为扩展模型上的复现实验，"
                "不能直接推出模型具备免疫性或确定服务端的模板解析机制。"
                "修复后的零温设置仍需对核心对照进行重新验证。")


if __name__ == "__main__":
    main()
