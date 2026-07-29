#!/usr/bin/env python3
"""Offline checks for the MaiBot M0/M1/M2 configuration-baseline files."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime"


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
        fail(f"缺少 {display_path(path)}；先运行 deploy/bootstrap.py")
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("m0", "m1", "m2"), default="m0")
    parser.add_argument("--compose", action="store_true", help="also validate docker-compose rendering")
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
    if args.compose:
        for image_variable in ("MAIBOT_IMAGE", "NAPCAT_IMAGE", "SQLITE_WEB_IMAGE"):
            if "@sha256:" not in env.get(image_variable, ""):
                fail(f"{image_variable} 必须锁定为 manifest digest")

    bot = read_toml(runtime / "core-config" / "bot_config.toml")
    model = read_toml(runtime / "core-config" / "model_config.toml")
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

    if bot.get("bot", {}).get("platform") != "qq":
        fail("bot.platform 必须为 qq")
    if bot.get("chat", {}).get("reply_timing", {}).get("talk_value") != 0.8:
        fail("talk_value 必须为 0.8")
    if bot.get("personality", {}).get("multiple_probability") != 0:
        fail("multiple_probability 必须为 0")
    if bot.get("chat", {}).get("reply_timing", {}).get("mentioned_bot_reply") is not True:
        fail("mentioned_bot_reply 必须为 true")
    if bot.get("chat", {}).get("reply_timing", {}).get("inevitable_at_reply") is not True:
        fail("inevitable_at_reply 必须为 true")
    if bot.get("chat", {}).get("reply_timing", {}).get("reply_trigger_mode") != "reply_necessity":
        fail("reply_trigger_mode 必须为 reply_necessity")
    if bot.get("chat", {}).get("reply_style", {}).get("enable_reply_quote") is not False:
        fail("enable_reply_quote 必须为 false")
    if bot.get("chat", {}).get("reply_timing", {}).get("max_consecutive_wait_count") != 3:
        fail("max_consecutive_wait_count 必须为 3")
    if bot.get("chat", {}).get("reply_timing", {}).get("no_action_backoff_base_seconds") != 30:
        fail("no_action_backoff_base_seconds 必须为 30")
    if bot.get("chat", {}).get("reply_timing", {}).get("no_action_backoff_cap_seconds") != 300:
        fail("no_action_backoff_cap_seconds 必须为 300")
    if bot.get("chat", {}).get("reply_timing", {}).get("enable_talk_value_rules") is not False:
        fail("enable_talk_value_rules 必须为 false")
    if bot.get("message_receive", {}).get("image_parse_threshold") != 1:
        fail("image_parse_threshold 必须为 1")
    if bot.get("message_receive", {}).get("ban_words") != []:
        fail("message_receive.ban_words 必须为空列表")
    keyword_reaction = bot.get("keyword_reaction", {})
    if keyword_reaction.get("keyword_rules") != [] or keyword_reaction.get("regex_rules") != []:
        fail("keyword_reaction 必须保持关闭")
    if bot.get("experimental", {}).get("emotion_trait") != "sentimental":
        fail("experimental.emotion_trait 必须为 sentimental")
    experimental = bot.get("experimental", {})
    if experimental.get("enable_behavior_learning") is not True:
        fail("experimental.enable_behavior_learning 必须为 true")
    if experimental.get("enable_rich_reply") is not True:
        fail("experimental.enable_rich_reply 必须为 true")
    if experimental.get("attention_drift", {}).get("enabled") is not False:
        fail("experimental.attention_drift.enabled 必须为 false")
    behavior_learning = experimental.get("behavior_learning_list", [])
    if (
        len(behavior_learning) != 1
        or behavior_learning[0].get("platform") != "qq"
        or behavior_learning[0].get("item_id") != env.get("PRODUCTION_GROUP_ID")
        or behavior_learning[0].get("type") != "group"
        or behavior_learning[0].get("use") is not True
        or behavior_learning[0].get("learn") is not True
    ):
        fail("行为学习必须只在生产群启用原生使用与学习")
    if bot.get("emoji", {}).get("emoji_send_num") != 25:
        fail("emoji_send_num 必须为 25")
    if bot.get("emoji", {}).get("max_reg_num") != 128:
        fail("max_reg_num 必须为 128")
    if bot.get("emoji", {}).get("do_replace") is not True:
        fail("do_replace 必须为 true")
    if bot.get("emoji", {}).get("check_interval") != 10:
        fail("check_interval 必须为 10")
    if bot.get("emoji", {}).get("max_emoji_size_mb") != 5:
        fail("max_emoji_size_mb 必须为 5")
    if bot.get("emoji", {}).get("cache_cleanup", {}).get("enabled") is not True:
        fail("emoji.cache_cleanup.enabled 必须为 true")
    if bot.get("emoji", {}).get("cache_cleanup", {}).get("check_interval_hours") != 24:
        fail("emoji.cache_cleanup.check_interval_hours 必须为 24")
    if bot.get("emoji", {}).get("cache_cleanup", {}).get("emoji_file_retention_days") != 30:
        fail("emoji.cache_cleanup.emoji_file_retention_days 必须为 30")
    if bot.get("emoji", {}).get("cache_cleanup", {}).get("no_file_record_retention_days") != 7:
        fail("emoji.cache_cleanup.no_file_record_retention_days 必须为 7")
    expression_learning = bot.get("expression", {}).get("learning_list", [])
    if (
        len(expression_learning) != 1
        or expression_learning[0].get("use") is not True
        or expression_learning[0].get("learn") is not True
    ):
        fail("expression.learning_list 必须只允许生产群使用并学习原生表达库")
    if bot.get("expression", {}).get("expression_checked_only") is not False:
        fail("expression_checked_only 必须为 false")
    if bot.get("expression", {}).get("expression_self_reflect") is not True:
        fail("expression_self_reflect 必须为 true")
    if bot.get("expression", {}).get("expression_selection_mode") != "vector":
        fail("expression_selection_mode 必须为 vector")
    if bot.get("expression", {}).get("expression_vector_candidate_pool_size") != 20:
        fail("expression_vector_candidate_pool_size 必须为 20")
    if bot.get("expression", {}).get("max_expression_learner") != 3:
        fail("max_expression_learner 必须为 3")
    jargon_learning = bot.get("jargon", {}).get("learning_list", [])
    if (
        len(jargon_learning) != 1
        or jargon_learning[0].get("use") is not True
        or jargon_learning[0].get("learn") is not True
    ):
        fail("jargon.learning_list 必须只允许生产群使用并学习原生黑话库")
    if bot.get("mcp", {}).get("enable") is not False:
        fail("v1 必须禁用 MCP")
    if bot.get("plugin", {}).get("permission") != []:
        fail("v1 不得配置基于 QQ 身份的插件权限")
    if bot.get("telemetry", {}).get("enable") is not False:
        fail("v1 必须关闭遥测")
    if bot.get("debug", {}).get("show_maisaka_thinking") is not False:
        fail("v1 不应记录思考过程")
    log = bot.get("log", {})
    if any(log.get(key) != "WARNING" for key in ("log_level", "console_log_level", "file_log_level")):
        fail("v1 日志级别必须为 WARNING，避免持久化不必要的聊天内容")
    if any(log.get(key) != 0 for key in ("llm_request_snapshot_limit", "maisaka_prompt_preview_limit", "maisaka_reply_effect_limit")):
        fail("v1 不得保留模型请求或 Prompt 预览快照")
    if webui_state.get("token_source") != "configured" or len(str(webui_state.get("access_token", ""))) < 20:
        fail("WebUI 必须在首次启动前使用独立的自定义 token")
    if napcat_webui.get("host") != "0.0.0.0" or napcat_webui.get("port") != 6099:
        fail("NapCat WebUI 必须使用镜像支持的内部监听配置")
    if len(str(napcat_webui.get("token", ""))) < 20:
        fail("NapCat WebUI 必须在首次启动前使用独立的自定义 token")
    if napcat_webui.get("loginRate") != 3:
        fail("NapCat WebUI 登录速率限制必须保持为 3")
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
    prompts = bot.get("chat", {}).get("reply_style", {}).get("chat_prompts", [])
    if not isinstance(prompts, list) or len(prompts) != 1:
        fail("必须只配置唯一生产群的行为提示")
    group_prompt = prompts[0].get("prompt", "")
    if "激进的投资策略煽动群聊" not in group_prompt:
        fail("生产群提示必须包含已保存的激进投资风格规则")
    names = {item.get("name") for item in model.get("models", [])}
    if "deepseek-v4-flash" not in names:
        fail("M0 需要 deepseek-v4-flash")
    tasks = model.get("model_task_config", {})
    if args.phase == "m1":
        if bot.get("emoji", {}).get("steal_emoji") is not True:
            fail("M1 必须启用表情包收集")
        if bot.get("emoji", {}).get("content_filtration") is not True:
            fail("M1 的表情包收集必须保持内容过滤")
        for name in ("qwen-vl", "qwen-embedding"):
            if name not in names:
                fail(f"M1 缺少模型：{name}")
        if names != {"deepseek-v4-flash", "qwen-vl", "qwen-embedding"}:
            fail("M1 只能加载 DeepSeek、Qwen-VL 与 Qwen embedding")
        provider_names = {item.get("name") for item in model.get("api_providers", [])}
        if provider_names != {"DeepSeek", "DashScope"}:
            fail("M1 只能配置既有 DeepSeek 与新增 DashScope 提供商")
        if tasks.get("vlm", {}).get("model_list") != ["qwen-vl"]:
            fail("M1 的 VLM 必须只配置 Qwen-VL")
        if tasks.get("embedding", {}).get("model_list") != ["qwen-embedding"]:
            fail("M1 的 embedding 必须显式选择 qwen-embedding")
    if args.phase == "m2":
        if bot.get("emoji", {}).get("steal_emoji") is not True:
            fail("M2 必须保持 M1 已启用的表情包收集")
        for name in ("qwen-vl", "qwen-embedding"):
            if name not in names:
                fail(f"M2 缺少模型：{name}")
        if names != {"deepseek-v4-flash", "qwen-vl", "qwen-embedding"}:
            fail("M2 只能加载 DeepSeek、Qwen-VL 与 Qwen embedding")
        provider_names = {item.get("name") for item in model.get("api_providers", [])}
        if provider_names != {"DeepSeek", "DashScope"}:
            fail("M2 只能配置 DeepSeek 与 DashScope 提供商")
        if tasks.get("vlm", {}).get("model_list") != ["qwen-vl"]:
            fail("M2 的 VLM 必须只配置 Qwen-VL")
        if tasks.get("embedding", {}).get("model_list") != ["qwen-embedding"]:
            fail("M2 的 embedding 必须显式选择 qwen-embedding")
    if args.phase in ("m1", "m2"):
        if bot.get("a_memorix", {}).get("plugin", {}).get("enabled") is not True:
            fail(f"{args.phase.upper()} 必须启用 A_Memorix")
        integration = bot.get("a_memorix", {}).get("integration", {})
        if any(integration.get(key) is not True for key in (
            "enable_memory_query_tool",
            "enable_person_profile_query_tool",
            "enable_person_profile_injection",
            "heuristic_memory_recall_enabled",
            "chat_summary_writeback_enabled",
            "person_fact_writeback_enabled",
        )):
            fail(f"{args.phase.upper()} 必须启用 A_Memorix 的查询、画像与自动写回集成")
        if integration.get("memory_query_default_limit") != 8:
            fail("A_Memorix memory_query_default_limit 必须为 8")
    else:
        if args.phase == "m0" and bot.get("emoji", {}).get("steal_emoji") is not False:
            fail("M0 不得启用表情包收集")
        a_memorix = bot.get("a_memorix", {})
        if a_memorix.get("plugin", {}).get("enabled") is not False:
            fail(f"{args.phase.upper()} 必须保持 A_Memorix 关闭")
        integration = a_memorix.get("integration", {})
        if any(integration.get(key) is not False for key in (
            "enable_memory_query_tool",
            "enable_person_profile_query_tool",
            "enable_person_profile_injection",
        )):
            fail(f"{args.phase.upper()} 必须关闭 A_Memorix 的全部集成入口")

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
