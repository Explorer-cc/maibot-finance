#!/usr/bin/env python3
"""无损重建 A_Memorix 的活动图快照。

仅在 Core 已停止且已经完成目录备份时运行。本工具绝不修改
metadata.db、向量索引、兼容图副本或旧快照；它只新建一代图快照，
并在全部验证通过后原子切换 graph_snapshot.json 指针。
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import uuid
from pathlib import Path

from scipy.sparse import load_npz


def read_object(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON 对象格式错误：{path}")
    return value


def fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def write_json_atomic(path: Path, payload: dict) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        if temporary.exists():
            temporary.unlink()


def fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser(description="无损重建 A_Memorix 活动图快照")
    parser.add_argument("--graph-dir", type=Path, default=Path("/MaiMBot/data/a-memorix/graph"))
    args = parser.parse_args()

    graph_dir = args.graph_dir.resolve()
    pointer_path = graph_dir / "graph_snapshot.json"
    compatibility_matrix = graph_dir / "graph_adjacency.npz"
    snapshots_root = graph_dir / "graph_snapshots"

    pointer = read_object(pointer_path)
    old_generation = str(pointer.get("generation", "")).strip()
    if not old_generation.startswith("graph-") or Path(old_generation).name != old_generation:
        raise RuntimeError("拒绝处理非法活动快照指针")
    old_snapshot = snapshots_root / old_generation
    old_metadata = read_object(old_snapshot / "graph_metadata.json")

    if not compatibility_matrix.is_file() or compatibility_matrix.stat().st_size == 0:
        raise RuntimeError("兼容图副本不存在或为空，拒绝猜测性恢复")
    matrix = load_npz(compatibility_matrix)
    expected_nodes = len(old_metadata.get("nodes", []))
    if matrix.shape != (expected_nodes, expected_nodes):
        raise RuntimeError(
            f"兼容图副本维度 {matrix.shape} 与活动元数据节点数 {expected_nodes} 不一致，拒绝切换"
        )

    new_generation = f"graph-repaired-{uuid.uuid4().hex}"
    temporary_dir = snapshots_root / f".{new_generation}.tmp"
    new_snapshot = snapshots_root / new_generation
    if temporary_dir.exists() or new_snapshot.exists():
        raise RuntimeError("新快照路径已存在，拒绝覆盖")

    temporary_dir.mkdir(parents=True)
    try:
        repaired_matrix = temporary_dir / "graph_adjacency.npz"
        with compatibility_matrix.open("rb") as source, repaired_matrix.open("wb") as destination:
            shutil.copyfileobj(source, destination, length=1024 * 1024)
            destination.flush()
            os.fsync(destination.fileno())
        if repaired_matrix.stat().st_size == 0:
            raise RuntimeError("复制后的图矩阵为空")
        reloaded = load_npz(repaired_matrix)
        if reloaded.shape != matrix.shape or reloaded.nnz != matrix.nnz:
            raise RuntimeError("复制后的图矩阵读回校验不一致")

        repaired_metadata = {**old_metadata, "snapshot_generation": new_generation, "has_adjacency": True}
        write_json_atomic(temporary_dir / "graph_metadata.json", repaired_metadata)
        fsync_directory(temporary_dir)
        os.replace(temporary_dir, new_snapshot)
        fsync_directory(snapshots_root)

        write_json_atomic(
            pointer_path,
            {"generation": new_generation, "schema_version": int(pointer.get("schema_version", 1))},
        )
    except BaseException:
        if temporary_dir.exists():
            shutil.rmtree(temporary_dir)
        raise

    print(
        "repaired_generation=" + new_generation
        + f" nodes={expected_nodes} nnz={matrix.nnz} matrix_bytes={compatibility_matrix.stat().st_size}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"repair refused: {exc}", file=sys.stderr)
        raise SystemExit(1)
