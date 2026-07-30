#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 0 ]]; then
  echo "用法：$0" >&2
  exit 2
fi

if [[ ! -x .venv/bin/python ]]; then
  echo "缺少 .venv；请先执行 uv venv --python 3.12 .venv 并安装依赖。" >&2
  exit 2
fi

bash ./scripts/host-check.sh
.venv/bin/python scripts/preflight.py --phase m2 --compose --public-admin
install -d -m 0700 \
  runtime/caddy-maibot/data runtime/caddy-maibot/config
if docker inspect maibot-public-admin >/dev/null 2>&1; then
  docker rm -f maibot-public-admin
fi
docker-compose --env-file .env -f compose.yaml --profile public-admin pull public-maibot-admin
docker-compose --env-file .env -f compose.yaml --profile public-admin up -d public-maibot-admin
docker-compose --env-file .env -f compose.yaml --profile public-admin ps public-maibot-admin
