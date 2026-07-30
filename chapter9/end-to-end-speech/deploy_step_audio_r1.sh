#!/usr/bin/env bash
set -euo pipefail

: "${STEP_AUDIO_MODEL_DIR:?Set STEP_AUDIO_MODEL_DIR to the downloaded stepfun-ai/Step-Audio-R1 directory}"
HERE="$(cd "$(dirname "$0")" && pwd)"

docker run --rm -ti --gpus all \
  -v "$STEP_AUDIO_MODEL_DIR:/Step-Audio-R1:ro" \
  -v "$HERE/chat_template.jinja:/chat_template.jinja:ro" \
  -p 9999:9999 \
  stepfun2025/vllm:step-audio-2-v20250909 \
  -- vllm serve /Step-Audio-R1 \
  --served-model-name Step-Audio-R1 \
  --port 9999 \
  --max-model-len 16384 \
  --max-num-seqs 32 \
  --tensor-parallel-size 4 \
  --chat-template /chat_template.jinja \
  --enable-log-requests \
  --interleave-mm-strings \
  --trust-remote-code
