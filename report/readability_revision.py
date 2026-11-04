"""Polish readability after report data and academic styles are generated."""
from docx.shared import Pt
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
REWRITES = {"2":"大语言模型智能体能够通过工具调用访问网页、邮件和业务系统，但工具返回的外部数据并不总是可信。攻击者若在其中植入恶意指令，智能体就可能把数据误认为应当执行的命令，从而遭受间接提示注入攻击。这类攻击的核心是混淆不同信息来源的可信边界：系统和用户可以下达指令，工具返回则主要提供数据。为区分不同来源，模型通常依据消息角色及指令优先级处理对话，而聊天模板负责组织这些角色标记。ChatInject 表明，攻击者可以在工具输出中伪造角色标记，使低可信内容看起来像高优先级消息，进而影响智能体的决策过程。","4":"Chang 等人在 ICLR 2026 发表的 ChatInject 研究，提出利用聊天模板实施间接提示注入，并比较普通文本注入、模板化注入、普通多轮注入和模板化多轮注入四种方式。作者还设计了 think 和 tool 两类辅助攻击。论文使用 AgentDojo 与 InjecAgent 两个基准，在九个模型上评估攻击成功率 ASR 和正常任务完成率 Utility。在 AgentDojo 上，平均 ASR 从 5.18% 提升至 32.05%；在 InjecAgent 上，则从 15.13% 提升至 45.90%。作者进一步发现，攻击可以在部分模型之间迁移，而部分检测器虽能降低攻击成功率，却可能影响正常任务的完成。","6":"本文围绕 ChatInject 开展代码复现，在 AgentDojo 基准上测试 DeepSeek、GLM-5.3-Flash 和 Qwen3.7-Flash 三个模型。实验包含七种攻击设置和一组无攻击基线，重点考察聊天模板、多轮对话和辅助攻击机制对攻击成功率与正常任务完成率的影响。第二章介绍复现过程与实验结果，后续章节由小组其他成员负责方法改进和进一步分析。","9":"本次复现主要检验三个问题：加入聊天模板是否能提高攻击成功率，多轮对话与模板组合是否会进一步增强攻击，以及攻击是否影响智能体完成正常任务。实验设置包括普通注入 S1、原生模板 ChatInject S2、think 钩子 S3、tool 钩子 S4、普通多轮注入 S5、多轮 ChatInject S6 和外来模板注入 S7，另设无攻击基线 S0。评测覆盖 AgentDojo 的银行、旅行和 Slack 三个任务域。攻击内容被植入账单、消息或评论等工具返回数据中，评测组合总数为 16×9 + 20×7 + 21×5 = 389，与原论文使用的测试规模一致。","10":"本次测试模型为 DeepSeek、GLM-5.3-Flash 和 Qwen3.7-Flash，其中 DeepSeek 使用的 API 模型标识为 deepseek-chat。这三个模型与原论文受试版本不同，因此本文主要比较各类攻击在不同模型上的效果趋势，不把跨版本结果差异直接解释为模型安全能力的变化。","12":"ChatInject 的核心思想是利用聊天模板实施间接提示注入。正常情况下，智能体从工具获得的文本属于低可信数据，不应改变系统指令或用户目标。攻击者在工具返回中嵌入 system、user、assistant 等角色标记，伪造具有高优先级的对话消息，使模型可能将数据误判为指令。其攻击过程如图 2-1 所示，图中机制依据原论文示意图重绘。","14":"图 2-1 ChatInject 攻击机制示意图","15":"论文从是否使用聊天模板、是否构造多轮对话两个维度设置四组对照。普通提示注入直接插入恶意文本；ChatInject 使用角色标记包装恶意指令；普通多轮攻击通过伪造历史对话增强诱导效果；多轮 ChatInject 则为每轮伪造对话添加模板标记。四组实验分别考察模板结构和多轮上下文的影响。此外，think 钩子通过伪造助手思考内容开展诱导，tool 钩子通过伪造工具调用内容测试模型是否会受预设执行过程影响。","17":"实验环境与任务配置见表 2-1。评测采用 AgentDojo 的银行、旅行和 Slack 三个任务域，三个模型使用相同的任务集合和自动判定流程，并通过各自服务商的 API 接口调用。实验统计攻击成功率 ASR 与正常任务完成率 Utility。需要说明的是，历史实验虽然在程序中将生成温度设置为 0，但这一参数并未实际传递给 API，因而可能使用了服务端默认采样配置。相关代码现已修复，核心实验结果仍需重新核验。","20":"本次复现以 ChatInject 作者发布的代码为基础，保留攻击内容构造、智能体工具交互和自动评测的主要流程。首先配置 AgentDojo 的银行、旅行和 Slack 三个任务域，并整理普通注入、模板注入、多轮攻击和辅助攻击等测试设置，保证三个模型采用一致的任务集合与评价标准。","21":"由于原始代码不能直接调用本次选用的三个模型，我们补充了 DeepSeek、智谱和阿里云百炼的接口适配，分别处理消息角色和工具调用格式。同时，根据各模型的聊天模板组织攻击内容，使不同模型能够使用相同的攻击构造流程。多轮攻击直接复用作者公开的七轮对话数据，以避免重新生成语料引入额外差异。","22":"执行实验时，我们修复了并行评测中的参数传递和失败状态记录问题，分别在三个任务域运行测试，并将智能体的工具调用轨迹及评测结果保存为 JSON 日志。每种攻击设置包含 389 个正式测试组合，另有 21 条攻击目标可行性校验记录。每个模型均完成七组攻击测试和一组无攻击测试。由于历史实验存在采样参数未传递的问题，本文保留实际测得的数据，并将参数修正后的重测列为后续工作。","24":"表 2-2 展示 DeepSeek 模型在 AgentDojo 三个任务域上的结果。ASR 与 Utility 均按正式测试样本数加权汇总，相关数值由实验日志自动计算得到。","26":"注：除无攻击基线的三域数据为 Utility 外，其余三域数据均为 ASR，单位为百分比。每组攻击包含 389 个正式测试组合；另外 21 条可行性校验日志不参与指标计算。","27":"表 2-3 对比原论文在 AgentDojo 上的代表性结果与本次 DeepSeek 实验。由于受试模型与接口配置不同，绝对数值不宜直接比较，重点应关注不同攻击方法带来的相对变化。","29":"注：本表均为 AgentDojo 基准上的攻击成功率 ASR，单位为百分比。原论文与本次实验使用的模型不同，结果仅供趋势比较。","30":"为了分析模型之间的差异，我们进一步在 GLM-5.3-Flash 和 Qwen3.7-Flash 上执行相同的七组攻击及无攻击基线。各攻击设置均包含 389 个正式测试组合，结果见表 2-4。由于三个模型均不同于原论文的受试版本，这里主要考察攻击效果的方向及相对增益。","32":"注：S1 为普通注入，S2 为原生模板注入，S3 和 S4 分别为 think 与 tool 钩子，S5 为普通多轮注入，S6 为多轮 ChatInject，S7 为外来模板注入。S1 至 S7 列为 ASR，末列为无攻击时的 Utility，单位均为百分比。","33":"在 Qwen3.7-Flash 上，普通注入的 ASR 为 5.1%，原生模板攻击提高至 9.5%，普通多轮攻击达到 14.7%，多轮与模板结合后进一步达到 21.6%，约为普通注入的 4.2 倍。使用 tool 钩子时，ASR 为 11.8%。上述结果与原论文中 Qwen 系列的变化趋势一致，但提升幅度明显较小。","34":"相比之下，DeepSeek 在不同攻击设置下的 ASR 为 2.8% 至 3.6%，GLM-5.3-Flash 为 0.3% 至 1.3%，均未观察到明显的模板化增益。三个模型面对相同攻击时表现不同，说明攻击效果可能受到模型及接口配置影响。但仅凭 ASR 无法判定差异是由模型训练、安全对齐、模板解析还是采样配置造成的。","35":"具体来看，DeepSeek 普通注入的 ASR 为 3.6%，原生模板攻击为 2.8%，并未出现原论文报告的显著提升。银行域在全部攻击设置下均为 0%。这一结果只反映当前实验条件，不能据此认定该模型能够抵御所有提示注入攻击。","36":"在 DeepSeek 上，普通多轮攻击的 ASR 为 2.8%，多轮 ChatInject 为 3.1%，仅提高 0.3 个百分点。think 钩子和 tool 钩子的 ASR 分别为 3.3% 和 3.1%。这些结果尚不足以证明多轮对话或辅助攻击能够稳定放大攻击效果。","37":"DeepSeek 在无攻击条件下的 Utility 为 91.2%，加入攻击后降至 74.0% 至 81.2%。Qwen3.7-Flash 的多轮 ChatInject 攻击成功率最高，达到 21.6%，此时 Utility 为 69.4%。这说明评估提示注入时不能只关注攻击成功率，还应同时考察对正常任务的干扰。","38":"跨模板实验中，使用 Qwen-3 模板攻击 DeepSeek 的 ASR 为 2.8%，与使用其原生模板的结果相同。但本次只测试了一种外来模板，尚不能据此否定 ChatInject 在其他模板与模型组合上的迁移能力。","40":"在复现范围上，本次实验仅覆盖 AgentDojo 的三个任务域和三个额外选取的模型，尚未测试 InjecAgent 基准，也未复现原论文的防御评测、模板相似度、模板混合和字符扰动实验。因此，不能把论文其他部分的结论视为本次复现结果。","41":"在实验可比性上，三个模型均不是原论文使用的相同版本，部分聊天模板还经过人工适配。此外，历史程序虽然将 temperature 设为 0，但实际调用时省略了该参数，需要在修复后重新运行核心对照，才能进一步判断结果是否稳定。","42":"在结果判定上，个别 Slack 用例虽然出现模型拒绝恶意请求的情况，但其转发的警告仍可能包含恶意链接，进而触发环境中的成功判定。因此，ASR 衡量的是攻击目标是否达成，并不必然表示模型主动遵从了恶意指令。总体而言，Qwen3.7-Flash 表现出与原论文一致的攻击增益趋势，而 DeepSeek 和 GLM-5.3-Flash 未观察到明显放大。这种差异可能与新模型的安全对齐、指令层级识别能力及 API 配置有关，目前仍属于有待验证的解释。"}
def apply_readability_revision(doc):
    if len(doc.paragraphs) < 43 or len(doc.tables) < 4:
        raise ValueError("Unexpected report structure; update readability map before rebuilding.")
    for raw_i, new_text in REWRITES.items():
        i = int(raw_i)
        p = doc.paragraphs[i]
        size = p.runs[0].font.size if p.runs else None
        font = p.runs[0].font.name if p.runs else None
        cjk = None
        if p.runs and p.runs[0]._element.rPr is not None and p.runs[0]._element.rPr.rFonts is not None:
            cjk = p.runs[0]._element.rPr.rFonts.get(qn("w:eastAsia"))
        p.text = new_text
        if size: p.runs[0].font.size = size
        if font: p.runs[0].font.name = font
        if cjk: p.runs[0]._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), cjk)
    doc.tables[1].rows[2].cells[0].text = "原生模板 ChatInject"
    doc.tables[1].rows[7].cells[0].text = "外来模板 ChatInject"
    doc.tables[3].rows[0].cells[0].text = "测试模型"
    doc.tables[0].rows[3].cells[1].text = "DeepSeek，接口标识 deepseek-chat；GLM-5.3-Flash；Qwen3.7-Flash"
    doc.tables[0].rows[6].cells[1].text = "攻击成功率 ASR；正常任务完成率 Utility"
    for cell in (doc.tables[1].rows[2].cells[0], doc.tables[1].rows[7].cells[0], doc.tables[3].rows[0].cells[0], doc.tables[0].rows[3].cells[1], doc.tables[0].rows[6].cells[1]):
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.name = "Times New Roman"
                run.font.size = Pt(10.5)
                run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "宋体")
    # The original bottom rule was attached to row 5 before two rows were appended.
    table = doc.tables[0]
    for i,row in enumerate(table.rows):
        for cell in row.cells:
            pr = cell._tc.get_or_add_tcPr()
            borders = pr.find(qn("w:tcBorders"))
            if borders is None:
                borders = OxmlElement("w:tcBorders")
                pr.append(borders)
            bottom = borders.find(qn("w:bottom"))
            if bottom is None:
                bottom = OxmlElement("w:bottom")
                borders.append(bottom)
            if i == len(table.rows)-1:
                bottom.set(qn("w:val"),"single")
                bottom.set(qn("w:sz"),"12")
                bottom.set(qn("w:color"),"000000")
            elif i > 0:
                bottom.set(qn("w:val"),"nil")
    # For the first two chapters, all parenthetical asides were rewritten.
    for p in doc.paragraphs:
        if p.style.name == "学术表题": p.paragraph_format.keep_with_next = True
    for p in doc.paragraphs:
        if any(c in p.text for c in "（）"):
            raise ValueError("Unpolished parenthetical phrase: "+p.text[:100])
