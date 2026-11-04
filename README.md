# ChatInject 论文复现：组员快速上手

本仓库用于《信息论》课程的 ChatInject 论文复现与分析。我们在作者提供的 AgentDojo 代码基础上，接入了三家模型 API，保存了已有实验轨迹，并编写了课程报告。**首次接手建议先复核已有结果，不要直接启动大规模付费实验。**

**入口**： [课程报告](课程报告.docx) · [详细实验手册](src/README.md) · [实验执行记录](results/执行记录.md) · [原论文与课堂资料](文章参考/) · [官方 ChatInject 仓库](https://github.com/hwanchang00/chatinject)

## 1. 目录与分工

| 路径 | 主要用途 |
|---|---|
| `src/agentdojo/` | 原框架和 ChatInject 攻击实现；`[chatinject-ext]` 为本项目扩展标记 |
| `src/run_batch.sh` | 运行三个任务域和七组攻击 + 无攻击基线 |
| `src/analyze_results.py` | 读取结果 JSON，统计 ASR、Utility 和模型间差异 |
| `src/check_results.py` | **离线校验**样本数量、日志数量和统计一致性 |
| `results/` | 已完成测试的分域汇总 JSON、episode 轨迹及执行记录 |
| `report/` | Word 报告的正文生成、图表和三线表排版程序 |
| `data/official_eval_results/` | 论文作者公开的参考实验数据 |
| `文章参考/` | 论文与课堂汇报材料 |
| `课程报告.docx` | 小组课程报告主文件；修改前先创建自己的本地副本 |

建议组员先阅读第 2 章实验复现，再重点看 `src/agentdojo/attacks/baseline_attacks.py` 和 `src/README.md`。

## 2. 五分钟上手：不调用付费 API

下面以 macOS / Linux / WSL 的 Bash 为例（需要有仓库访问权限）。

```bash
git clone git@github.com:TL-SN/chatinject-reproduction.git
cd chatinject-reproduction

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r src/requirements.txt

# 直接验证已有实验，无需 API Key
python src/check_results.py
python src/analyze_results.py --compare
```

成功后可以看到三个模型的汇总统计与论文参考数据。**建议优先在已保存的 JSON 上完成结果分析和图表制作**，不必每次重新请求模型。

更新数据或报告脚本后，在项目根目录运行：

```bash
python report/write_report.py
```

该命令会重新写入 `课程报告.docx` 的前两章。请先自行备份或使用新分支；第三章及以后的组员内容不应被自动替换。文档渲染效果可以查看 `report/review_contact.png`，也可用 Word 或 LibreOffice 检查。

## 3. 实验设计与已有结果

三个任务域：banking、travel、slack。每个攻击配置含 **389 个正式评测组合**，另有 21 条注入目标可行性校验日志；无攻击基线为 57 个任务。

| 设置 | 说明 |
|---|---|
| S1 | 普通文本提示注入 |
| S2 | 原生聊天模板 ChatInject |
| S3 / S4 | ChatInject + think / tool 钩子 |
| S5 | 普通多轮提示注入 |
| S6 | 多轮 ChatInject |
| S7 | 使用外来模型聊天模板 |
| S0 | 无攻击基线，测试正常任务完成率 |

指标：**ASR** 表示攻击目标达成比例，越低表示越难被攻击；**Utility** 表示正常用户任务完成比例，越高越好。

| 历史日志标识 | S1 ASR | S2 ASR | S6 ASR | S0 Utility |
|---|---:|---:|---:|---:|
| `deepseek-chat` | 3.6% | 2.8% | 3.1% | 91.2% |
| `glm-5.3-flash` | 0.3% | 0.3% | 1.3% | 87.7% |
| `qwen3.7-flash` | 5.1% | 9.5% | 21.6% | 87.7% |

数据来自仓库既有实验记录，**不是重新运行所得**。报告中的 DeepSeek-V4-Flash 是项目使用的展示名称；历史 API 请求及日志使用 `deepseek-chat`。**具体服务端模型版本不能仅凭该请求标识确定，需对照原始 API 响应或服务商记录核验。**

注意：原始实验在程序中写了 `temperature=0`，但旧代码未将这一参数实际发送至 API。该错误已修复，**历史结果不能视为严格零温度复现，修复后需要重新跑核心对照才能验证结果稳定性**。

## 4. 需要执行新实验时

先配置密钥。**不要提交密钥、代理凭据或包含敏感内容的日志**。`api_key.txt` 已加入 `.gitignore`。支持两种方式：

```bash
# 方式 A：环境变量（更推荐）
export DEEPSEEK_API_KEY="你的密钥"
export ZHIPU_API_KEY="你的密钥"
export DASHSCOPE_API_KEY="你的密钥"
```

或在仓库根目录新建 `api_key.txt`，每行一个：`deepseek: xxx`、`glm: xxx`、`qwen: xxx`。仅需配置实际测试的服务商。

**先做单组验证**（从仓库根目录执行；示例使用 DeepSeek 兼容接口）：

```bash
cd src
python -m agentdojo.scripts.benchmark \
  --model DEEPSEEK_CHAT \
  -s banking -s travel -s slack \
  --attack chat_inject_deepseek \
  --max-workers 3 \
  --logdir ../results/rerun_example/deepseek_chat_inject/logs \
  --eval-results-dir ../results/rerun_example/deepseek_chat_inject
cd ..
```

需要完整七组攻击及基线时，可执行 `MODEL=deepseek bash src/run_batch.sh`、`MODEL=glm5f bash src/run_batch.sh` 或 `MODEL=qwen37f bash src/run_batch.sh`。**批处理默认使用历史 `results/` 路径并支持断点续跑，已有文件可能导致跳过样本；切换模型参数或修复代码后，请先修改输出目录或使用新的日志目录，切勿混合新旧实验配置。** 完整命令和踩坑记录见 [src/README.md](src/README.md)。

## 5. 开展后续改进的推荐流程

1. **明确假设**：改进攻击构造、策略或防御机制时，先定义要比较的设置与预期影响。
2. **固定环境与分母**：同一模型、任务集合和指标口径下跑基线和改进方法，保存 API 型号、日期、采样参数及配置。
3. **先少量验证，再批量执行**：使用独立结果目录，避免影响已有数据。API 费用和服务端限流需由实验人员自行控制。
4. **自动统计 + 人工抽查**：运行分析脚本，并检查成功案例是否真的符合攻击目标；不要只依赖 ASR 百分比。
5. **更新报告**：明确区分论文原始数据、历史复现结果和新增实验；对于模型增强、安全对齐、模板解析等解释，在没有机制实验时只写为假设。

**当前复现范围**：AgentDojo 三个任务域、三款额外测试模型；尚未复现 InjecAgent 基准、防御评测、模板相似度和扰动实验。实验结果的跨模型差异不等于已经证明模型“免疫”。

## 6. 常见问题

- **安装后找不到 `agentdojo`**：请先 `cd src` 再运行 `python -m agentdojo.scripts.benchmark`，或执行仓库根目录的脚本入口。
- **429 / RateLimitError**：服务商限流；检查失败日志后重试。批处理可复用相同日志目录断点续跑，但应先确认参数未变。
- **389 vs 410**：389 是正式 ASR 评测分母，410 是包含 21 条可行性校验的日志数，不应直接使用 410 计算 ASR。
- **报告和 JSON 不一致**：先看 `results/执行记录.md` 和 `src/analyze_results.py`；不要手工改表格数值后忘记修改生成脚本。
- **模型名称变化**：首先检查 `src/agentdojo/models.py` 与真实 API 响应，不要直接把 provider 的模型别名当成固定版本。

组员修改时优先新开分支，通过 Pull Request 合并；对结果、报告和代码都保留可追溯记录。
