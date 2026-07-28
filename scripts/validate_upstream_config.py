#!/usr/bin/env python3
"""Validate rendered TOML with the pinned MaiBot source's Pydantic models."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    payload.pop("inner", None)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, required=True)
    parser.add_argument("--maibot-source", type=Path, required=True)
    args = parser.parse_args()
    source = args.maibot_source.resolve()
    runtime = args.runtime_dir.resolve()
    if not (source / "src" / "config" / "config.py").exists():
        parser.error("--maibot-source 必须指向 MaiBot 源码根目录")
    sys.path.insert(0, str(source))
    from src.config.config import Config, ModelConfig  # noqa: PLC0415

    Config(**load(runtime / "core-config" / "bot_config.toml"))
    ModelConfig(**load(runtime / "core-config" / "model_config.toml"))
    print("PASS: MaiBot 上游配置模型验证通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
