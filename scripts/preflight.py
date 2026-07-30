#!/usr/bin/env python3
"""Offline checks for the MaiBot M0/M1/M2 configuration-baseline files."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"
PUBLIC_ADMIN_REQUIRED = (
    "CADDY_IMAGE",
    "MAIBOT_ADMIN_USER",
    "MAIBOT_ADMIN_PASSWORD_HASH",
)
PLACEHOLDER = {"", "CHANGE_ME", "TODO", "REPLACE_ME"}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_toml(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"缺少 {display_path(path)}；首次部署请运行 deploy/bootstrap.py --initialize")
    except tomllib.TOMLDecodeError as error:
        fail(f"{display_path(path)} 不是合法 TOML：{error}")


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        fail("缺少 .env")
    for line in lines:
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def validate_public_admin(env: dict[str, str]) -> None:
    missing = [name for name in PUBLIC_ADMIN_REQUIRED if env.get(name, "").upper() in PLACEHOLDER]
    if missing:
        fail("公网管理入口缺少 .env 配置：" + ", ".join(missing))
    for name in ("MAIBOT_ADMIN_USER",):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", env[name]):
            fail(f"{name} 只能使用 1-64 位字母、数字、下划线或连字符")
    for name in ("MAIBOT_ADMIN_PASSWORD_HASH",):
        if not re.fullmatch(r"\$2[aby]\$[0-9]{2}\$[./A-Za-z0-9]{53}", env[name]):
            fail(f"{name} 必须是标准 bcrypt 哈希")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("m0", "m1", "m2"), default="m0")
    parser.add_argument("--compose", action="store_true", help="also validate docker-compose rendering")
    parser.add_argument("--public-admin", action="store_true", help="validate the optional public admin proxy")
    parser.add_argument("--env-file", type=Path, default=ROOT / ".env")
    parser.add_argument("--runtime-dir", type=Path, default=RUNTIME)
    args = parser.parse_args()
    runtime = args.runtime_dir.resolve()

    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")
    for required in (
        "127.0.0.1:${WEBUI_PORT}",
        "127.0.0.1:${NAPCAT_WEBUI_PORT}",
        "profiles: [\"admin\"]",
        'driver: "none"',
    ):
        if required not in compose:
            fail(f"compose.yaml 缺少安全约束：{required}")
    if ":latest" in compose:
        fail("compose.yaml 不得硬编码 latest；镜像由 .env 锁定")

    env = read_env(args.env_file.resolve())
    if args.public_admin:
        for required in (
            'profiles: ["public-admin"]',
            "public-maibot-admin:",
            "${PUBLIC_HTTP_PORT:-8080}:80",
        ):
            if required not in compose:
                fail(f"compose.yaml 缺少公网管理入口约束：{required}")
        validate_public_admin(env)
    if args.compose:
        image_variables = ["MAIBOT_IMAGE", "NAPCAT_IMAGE", "SQLITE_WEB_IMAGE"]
        if args.public_admin:
            image_variables.append("CADDY_IMAGE")
        for image_variable in image_variables:
            if "@sha256:" not in env.get(image_variable, ""):
                fail(f"{image_variable} 必须锁定为 manifest digest")

    read_toml(runtime / "core-config" / "bot_config.toml")
    read_toml(runtime / "core-config" / "model_config.toml")
    adapter = read_toml(runtime / "data" / "MaiMBot" / "plugins" / "MaiBot-Napcat-Adapter" / "config.toml")
    webui_state_path = runtime / "data" / "MaiMBot" / "webui.json"
    napcat_webui_path = runtime / "napcat-config" / "webui.json"
    napcat_onebot_path = runtime / "napcat-config" / "onebot11.json"
    try:
        webui_state = json.loads(webui_state_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError) as error:
        fail(f"缺少或无效的 WebUI 状态文件：{error}")
    try:
        napcat_webui = json.loads(napcat_webui_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError) as error:
        fail(f"缺少或无效的 NapCat WebUI 配置：{error}")
    try:
        napcat_onebot = json.loads(napcat_onebot_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError) as error:
        fail(f"缺少或无效的 NapCat OneBot 配置：{error}")

    if webui_state.get("token_source") != "configured" or len(str(webui_state.get("access_token", ""))) < 20:
        fail("WebUI 必须在首次启动前使用独立的自定义 token")
    if napcat_webui.get("host") != "0.0.0.0" or napcat_webui.get("port") != 6099:
        fail("NapCat WebUI 必须使用镜像支持的内部监听配置")
    if len(str(napcat_webui.get("token", ""))) < 20:
        fail("NapCat WebUI 必须在首次启动前使用独立的自定义 token")
    websocket_servers = napcat_onebot.get("network", {}).get("websocketServers", [])
    if len(websocket_servers) != 1:
        fail("NapCat 必须只配置一个正向 WebSocket 服务")
    websocket_server = websocket_servers[0]
    if (
        websocket_server.get("enable") is not True
        or websocket_server.get("host") != "0.0.0.0"
        or websocket_server.get("port") != 3001
        or websocket_server.get("token") != env.get("NAPCAT_WS_TOKEN")
    ):
        fail("NapCat 正向 WebSocket 必须在 3001 使用与 .env 一致的 token")
    if websocket_server.get("reportSelfMessage") is not False:
        fail("NapCat 不得上报自身消息")
    if adapter.get("chat", {}).get("group_list_type") != "whitelist" or not adapter.get("chat", {}).get("group_list"):
        fail("NapCat 适配器必须使用非空群白名单")
    if adapter.get("chat", {}).get("private_list") != []:
        fail("v1 不应开放普通私聊")
    if adapter.get("filters", {}).get("ignore_self_message") is not True:
        fail("必须过滤机器人自身消息")
    if adapter.get("napcat_server", {}).get("host") != "napcat":
        fail("适配器必须直接连接内部 napcat 服务")
    if args.compose:
        compose_command = shutil.which("docker-compose")
        if not compose_command:
            fail("未找到 docker-compose")
        result = subprocess.run(
            [compose_command, "--env-file", str(args.env_file.resolve()), "-f", "compose.yaml", "config"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        if result.returncode:
            fail("docker-compose config 失败：" + result.stderr.strip())
    print(f"PASS: {args.phase.upper()} 配置结构与安全基线已通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
