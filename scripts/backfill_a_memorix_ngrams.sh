#!/usr/bin/env bash
# 对现有 A_Memorix paragraph 进行一次性 ngram 倒排索引回填。
#
# 该操作只写入 paragraph_ngrams 与 paragraph_ngram_meta；不改 paragraph、向量、
# 图谱或 episode。必须在 maibot-core 已停止时执行，避免绕过 A_Memorix 的单写者锁。

set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

if [[ "${1:-}" != "--apply" || $# -ne 1 ]]; then
  cat <<'USAGE'
用法：scripts/backfill_a_memorix_ngrams.sh --apply

执行前：
  1. 在低活跃窗口停止 maibot-core（SnowLuma 可保持运行）。
  2. 为 runtime/data/MaiMBot/a-memorix/ 创建私有备份。

脚本会拒绝在 maibot-core 仍运行时执行。
USAGE
  exit 2
fi

running=$(docker inspect --format '{{.State.Running}}' maibot-core 2>/dev/null) \
  || fail '找不到 maibot-core 容器；请先用当前 Compose 创建容器。'
[[ "$running" == "false" ]] || fail 'maibot-core 仍在运行；请先停止 Core，不能绕过 A_Memorix 单写者锁。'

image=$(docker inspect --format '{{.Config.Image}}' maibot-core 2>/dev/null) \
  || fail '无法读取 maibot-core 的镜像。'
[[ -n "$image" ]] || fail 'maibot-core 未记录镜像引用。'

data_dir="$ROOT_DIR/runtime/data/MaiMBot"
[[ -d "$data_dir/a-memorix/metadata" ]] || fail "缺少 A_Memorix 元数据目录：$data_dir/a-memorix/metadata"
config_dir="$ROOT_DIR/runtime/core-config"
[[ -d "$config_dir" ]] || fail "缺少 Core 配置目录：$config_dir"

# 不使用宿主机 Python 或手写 SQL：必须在与 Core 相同的镜像和虚拟环境中调用
# MetadataStore 的事务、schema 与 ngram 实现。
docker run --rm \
  --network none \
  --workdir /MaiMBot \
  --env PYTHONDONTWRITEBYTECODE=1 \
  --env OPENBLAS_NUM_THREADS=1 \
  --env OMP_NUM_THREADS=1 \
  --env MKL_NUM_THREADS=1 \
  --volume "$data_dir:/MaiMBot/data" \
  --volume "$config_dir:/MaiMBot/config:ro" \
  --entrypoint /MaiMBot/.venv/bin/python \
  "$image" -c '
from pathlib import Path

from src.A_memorix.core.storage.metadata_store import MetadataStore

metadata_dir = Path("/MaiMBot/data/a-memorix/metadata")
store = MetadataStore(data_dir=metadata_dir)
store.connect(enforce_schema=True)
try:
    conn = store._resolve_conn()
    store.ensure_paragraph_ngram_schema(conn=conn)
    if not store.ensure_paragraph_ngram_backfilled(n=2, conn=conn):
        raise RuntimeError("ngram 回填返回失败")

    active = int(conn.execute(
        "SELECT COUNT(1) FROM paragraphs WHERE is_deleted IS NULL OR is_deleted = 0"
    ).fetchone()[0])
    indexed = int(conn.execute(
        "SELECT COUNT(DISTINCT paragraph_hash) FROM paragraph_ngrams"
    ).fetchone()[0])
    if not store.is_paragraph_ngram_ready(n=2, conn=conn):
        raise RuntimeError("ngram 索引元数据未就绪")
    if indexed != active:
        raise RuntimeError(f"ngram 覆盖不完整：active={active}, indexed={indexed}")
    print(f"PASS: ngram 回填完成；active_paragraphs={active}, indexed_paragraphs={indexed}")
finally:
    store.close()
'
