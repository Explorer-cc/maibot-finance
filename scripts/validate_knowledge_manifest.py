#!/usr/bin/env python3
"""Validate the metadata and checksum of an M3 static-knowledge manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


ALLOWED_DOMAINS = {"common", "crypto"}
ALLOWED_TRUST_LEVELS = {"primary", "official_education", "secondary"}
ALLOWED_STATUSES = {"active", "deprecated"}
SHA256 = re.compile(r"[0-9a-f]{64}")


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_text(payload: dict, field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip() or value.startswith("Replace with"):
        fail(f"{field} 必须是非空文本")
    return value.strip()


def require_date(payload: dict, field: str, *, allow_null: bool = False) -> date | None:
    value = payload.get(field)
    if value is None and allow_null:
        return None
    if not isinstance(value, str):
        fail(f"{field} 必须是 YYYY-MM-DD 日期")
    try:
        return date.fromisoformat(value)
    except ValueError:
        fail(f"{field} 必须是 YYYY-MM-DD 日期")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        fail(f"无法读取 manifest：{error}")
    if not isinstance(payload, dict):
        fail("manifest 根节点必须是 JSON 对象")

    for field in ("id", "title", "author_or_institution", "version", "license"):
        require_text(payload, field)
    if payload.get("domain") not in ALLOWED_DOMAINS:
        fail("domain 只能是 common 或 crypto")
    if payload.get("trust_level") not in ALLOWED_TRUST_LEVELS:
        fail("trust_level 不在允许列表中")
    if payload.get("status") not in ALLOWED_STATUSES:
        fail("status 只能是 active 或 deprecated")

    source_url = require_text(payload, "source_url")
    if urlparse(source_url).scheme != "https" or not urlparse(source_url).netloc:
        fail("source_url 必须是 HTTPS URL")
    require_text(payload, "jurisdiction")
    published_at = require_date(payload, "published_at")
    imported_at = require_date(payload, "imported_at")
    valid_from = require_date(payload, "valid_from")
    valid_until = require_date(payload, "valid_until", allow_null=True)
    if valid_until is not None and valid_from is not None and valid_until < valid_from:
        fail("valid_until 不能早于 valid_from")
    if published_at is not None and imported_at is not None and imported_at < published_at:
        fail("imported_at 不能早于 published_at")

    content_file = require_text(payload, "content_file")
    content_path = (manifest_path.parent / content_file).resolve()
    if content_path.parent != manifest_path.parent or not content_path.is_file():
        fail("content_file 必须是与 manifest 同目录的现有普通文件")
    expected_sha256 = require_text(payload, "content_sha256").lower()
    if not SHA256.fullmatch(expected_sha256):
        fail("content_sha256 必须是 64 位小写 SHA-256")
    actual_sha256 = hashlib.sha256(content_path.read_bytes()).hexdigest()
    if actual_sha256 != expected_sha256:
        fail("content_sha256 与资料文件不匹配")

    print(f"PASS: {payload['id']} 元数据和文件校验通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
