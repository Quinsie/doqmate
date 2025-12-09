#!/bin/bash
#
# runModelServer.sh
# Qwen2.5-7B-Instruct vLLM 서버 + bge-m3 임베딩 서버 실행 스크립트
#
# how to use
#   1) chmod +x services/runModelServer.sh
#   2) ./services/runModelServer.sh

# Activate environment
source ~/anaconda3/etc/profile.d/conda.sh
conda activate llm_server

LOG_DIR="data/logs/model"
TODAY=$(date +%F)

mkdir -p "${LOG_DIR}"

VLLM_LOG="${LOG_DIR}/${TODAY}_LLM.log"
EMB_LOG="${LOG_DIR}/${TODAY}_embedding.log"

echo "[INFO] vLLM log file      : ${VLLM_LOG}"
echo "[INFO] Embedding log file : ${EMB_LOG}"

# Launch vLLM server
nohup python -m vllm.entrypoints.openai.api_server \
  --model /home/jiho/doqmate/doqmate/models/Qwen \
  --served-model-name qwen2.5-7b-instruct \
  --port 11400 \
  --dtype float16 \
  --tensor-parallel-size 1 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.7 \
  --max-num-seqs 32 \
  >> "${LOG_DIR}/vllm.log" 2>&1 &

VLLM_PID=$!
echo "[OK] vLLM server launched on port 11400 (PID: ${VLLM_PID})"

# Launch embedding server
nohup python3 -m services.embedding.embeddingServer \
  >> "${LOG_DIR}/embedding.log" 2>&1 &

EMB_PID=$!
echo "[OK] Embedding server launched on port 11401 (PID: ${EMB_PID})"

echo "[DONE] All model servers launched."