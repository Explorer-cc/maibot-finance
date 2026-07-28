#!/usr/bin/env bash
set -euo pipefail

docker-compose --env-file .env -f compose.yaml down
