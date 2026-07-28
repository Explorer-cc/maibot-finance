#!/usr/bin/env bash
set -euo pipefail

phase="${1:-m0}"
if [[ "$phase" != "m0" && "$phase" != "m2" ]]; then
  echo "用法：$0 [m0|m2]" >&2
  exit 2
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "缺少 .venv；请先执行 uv venv --python 3.12 .venv 并安装依赖。" >&2
  exit 2
fi

bash ./scripts/host-check.sh
.venv/bin/python deploy/bootstrap.py --phase "$phase"
.venv/bin/python scripts/preflight.py --phase "$phase" --compose
docker-compose --env-file .env -f compose.yaml pull
docker-compose --env-file .env -f compose.yaml up -d --remove-orphans
docker-compose --env-file .env -f compose.yaml ps
