#!/usr/bin/env bash
# Verify the Debian host prerequisites required to start the pinned containers.
set -euo pipefail

for command in docker docker-compose apparmor_parser; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "缺少主机依赖：$command" >&2
    exit 2
  fi
done

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon 不可用；请启动 Docker 后重试。" >&2
  exit 2
fi

docker-compose version >/dev/null
echo "PASS: Docker、Compose 与 AppArmor parser 可用"
