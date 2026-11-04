#!/usr/bin/env bash
# ChatInject 复现主实验批处理（并行版）
# 基准: AgentDojo v1.2.1 banking/travel/slack（389 例/设置）
#
# 用法（在 src/ 下执行）:
#   nohup bash run_batch.sh > ../results/logs/batch.log 2>&1 &   # 默认 DeepSeek
#   MODEL=zhipu  nohup bash run_batch.sh > ../results/logs/batch_zhipu.log 2>&1 &   # 智谱 GLM-4.5（已被平台下线，仅供留档）
#   MODEL=qwen   nohup bash run_batch.sh > ../results/logs/batch_qwen.log 2>&1 &    # 百炼 Qwen3-235B（已被平台下线，仅供留档）
#   MODEL=glm5f  nohup bash run_batch.sh > ../results/logs/batch_glm5f.log 2>&1 &   # 智谱 GLM-5.3-Flash（免费档，2026-11 增补）
#   MODEL=qwen37f nohup bash run_batch.sh > ../results/logs/batch_qwen37f.log 2>&1 & # 百炼 Qwen3.7-Flash（低价档，2026-11 增补）
#
# key 统一放 ../api_key.txt，每行 "provider: key"（deepseek / glm / qwen）。
set -u
cd "$(dirname "$0")"

# ---- 从 api_key.txt 导出全部已配置的 key（缺哪个自动跳过对应模型）----
export DEEPSEEK_API_KEY=$(grep '^deepseek:' ../api_key.txt 2>/dev/null | head -1 | cut -d':' -f2- | tr -d ' ')
export ZHIPU_API_KEY=$(grep -E '^(glm|zhipu):' ../api_key.txt 2>/dev/null | head -1 | cut -d':' -f2- | tr -d ' ')
export DASHSCOPE_API_KEY=$(grep -E '^(qwen|dashscope):' ../api_key.txt 2>/dev/null | head -1 | cut -d':' -f2- | tr -d ' ')

# ---- 选择受试模型（默认 deepseek），并按模型选对应的"原生模板"攻击矩阵 ----
MODEL=${MODEL:-deepseek}
case "$MODEL" in
  deepseek)
    MODEL_ENUM=DEEPSEEK_CHAT; MODEL_NAME=deepseek-chat
    CI_NATIVE=chat_inject_deepseek;                    # 原生模板 ChatInject
    CI_THINK=chat_inject_deepseek_think; CI_TOOL=chat_inject_deepseek_tool
    MT_NATIVE=chat_inject_deepseek_with_utility_system_multiturn_7 ;;
  zhipu)
    MODEL_ENUM=ZHIPU_GLM_4_5; MODEL_NAME=glm-4.5
    CI_NATIVE=chat_inject_glm;                         # 官方实现的 GLM 原生模板
    CI_THINK=chat_inject_glm_think; CI_TOOL=chat_inject_glm_tool
    MT_NATIVE=chat_inject_glm_with_utility_system_multiturn_7 ;;
  qwen)
    MODEL_ENUM=DASHSCOPE_QWEN3_235B; MODEL_NAME=qwen3-235b-a22b
    CI_NATIVE=chat_inject_qwen3;                       # 官方实现的 Qwen-3 原生模板
    CI_THINK=chat_inject_qwen3_think; CI_TOOL=chat_inject_qwen3_tool
    MT_NATIVE=chat_inject_qwen3_with_utility_system_multiturn_7 ;;
  glm5f)                                               # [chatinject-ext] 2026-11: 论文原模型已下线，改用同厂继任代
    MODEL_ENUM=ZHIPU_GLM_5_3_FLASH; MODEL_NAME=glm-5.3-flash
    CI_NATIVE=chat_inject_glm5;                        # GLM-5.x 模板（对 GLM-5.3 tokenizer 实测核对）
    CI_THINK=chat_inject_glm5_think; CI_TOOL=chat_inject_glm5_tool
    MT_NATIVE=chat_inject_glm5_with_utility_system_multiturn_7 ;;
  qwen37f)
    MODEL_ENUM=DASHSCOPE_QWEN3_7_FLASH; MODEL_NAME=qwen3.7-flash
    CI_NATIVE=chat_inject_qwen3;                       # Qwen3.5/3.7 仍为 ChatML，官方 qwen3 模板即原生
    CI_THINK=chat_inject_qwen3_think; CI_TOOL=chat_inject_qwen3_tool
    MT_NATIVE=chat_inject_qwen3_with_utility_system_multiturn_7 ;;
  *) echo "未知 MODEL=$MODEL（可选 deepseek/zhipu/qwen/glm5f/qwen37f）"; exit 1 ;;
esac
echo "受试模型: $MODEL_NAME ($MODEL_ENUM)"

PY=/home/tlsn/.venvs/chatinject/bin/python
RES=../results

run_attack () {  # $1=attack name
  local atk="$1"
  echo "[$(date '+%F %T')] START attack=$atk"
  $PY -m agentdojo.scripts.benchmark \
      --model "$MODEL_ENUM" \
      -s banking -s travel -s slack \
      --attack "$atk" \
      --max-workers 3 \
      --logdir "$RES/${MODEL_NAME}_${atk}/logs" \
      --eval-results-dir "$RES/${MODEL_NAME}_${atk}"
  ec=$?
  echo "[$(date '+%F %T')] DONE attack=$atk (exit=$ec)"
}

# 第一波：核心四变体（论文 Table 1 的四列），两两并行
run_attack "injecagent" &
run_attack "$CI_NATIVE" &
wait
run_attack "injecagent_with_utility_system_multiturn_7" &
run_attack "$MT_NATIVE" &
wait

# 第二波：外来模板迁移（与原生不同家的模板）+ 钩子
case "$MODEL" in
  deepseek) FOREIGN=chat_inject_qwen3 ;;   # qwen3 模板 → deepseek
  zhipu)    FOREIGN=chat_inject_qwen3 ;;   # qwen3 模板 → glm（亦可用 chat_inject_kimi_k2）
  qwen)     FOREIGN=chat_inject_glm ;;     # glm 模板 → qwen
  glm5f)    FOREIGN=chat_inject_qwen3 ;;   # qwen3 模板 → glm-5.3-flash
  qwen37f)  FOREIGN=chat_inject_glm ;;     # glm 模板 → qwen3.7-flash
esac
run_attack "$FOREIGN" &
run_attack "$CI_TOOL" &
wait
run_attack "$CI_THINK" &

# 无攻击 benign utility 基线（仅 57 个用户任务，串行收尾）
$PY -m agentdojo.scripts.benchmark \
    --model "$MODEL_ENUM" \
    -s banking -s travel -s slack \
    --max-workers 3 \
    --logdir "$RES/${MODEL_NAME}_noattack/logs" \
    --eval-results-dir "$RES/${MODEL_NAME}_noattack"
echo "[$(date '+%F %T')] DONE noattack (exit=$?)"
wait
echo "[$(date '+%F %T')] ALL RUNS COMPLETE"
