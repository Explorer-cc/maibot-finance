# 当前运行事项与私有配置说明

本文件说明已有实例的配置边界和仍需记录的验证事实。不得在本文件、提交记录、工单或聊天记录中填入密钥、群号、二维码、QQ 登录态或聊天正文。

## 当前已固定的私有配置

- `.env` 中锁定 MaiBot、NapCat、sqlite-web 与 Caddy 的镜像 digest；不得改为 tag 或 `latest`。
- Core WebUI、NapCat WebUI 与 sqlite-web 保持服务器回环绑定；既有 SSH 转发保持不变。
- SnowLuma WebUI `5099` 与 noVNC `6081` 均固定绑定服务器回环；noVNC 用于日常本机或 SSH 隧道维护，不得映射到公网。
- 唯一生产群、WebUI Token、NapCat WebUI Token 和内部 WebSocket Token 均为私有值，不得复用或外泄。
- DeepSeek 与 DashScope 凭据只保存在 `.env`；模型名称和 embedding 配置以当前运行值为准。
- Adapter 当前拒绝普通私聊和第二个群，MCP 保持关闭；但已启用联网搜索、外部图片下载、EXIF 定位和群聊分析插件。不要将本实例描述为没有联网或外部工具。

## 日常操作

查看状态：

```bash
docker-compose --env-file .env -f compose.yaml ps
```

确认 Core 与 SnowLuma 已启动（显式服务名，绝不拉起 NapCat）：

```bash
docker-compose --env-file .env -f compose.yaml --profile snowluma up -d core snowluma
```

这两个命令使用现有 `runtime/`，不重置配置。不要为日常运维运行 `deploy/bootstrap.py`，也不要执行 `--reset-config --yes-reset-config`。

### 2026-09-14 后的链路核验与两类偶发故障恢复

`docker-compose ps` 显示 `healthy` 只代表 Core WebUI HTTP 可达，不代表消息链路可用。链路完整核验依次为：

1. SnowLuma 日志（`runtime/snowluma/data/logs/`）当日文件出现 `login detected` 与 `[OneBot.WS-Server] [ws-default] listening 0.0.0.0:3001`。
2. Core 容器内存在到 `snowluma:3001` 的 ESTABLISHED 连接（适配器已回连）。
3. Core 容器内存在存活的 `runner_main` 进程与已连接的 `/tmp/maibot-plugin-*.sock`（插件运行时正常）。

两类已验证的偶发故障与恢复手段：

- SnowLuma QQ 卡在 `login identity discovered; awaiting readiness`、`LoginProbe` 超时、`3001` 不监听 → `docker restart maibot-snowluma` 重试 Hook 注入，约 30 秒内恢复，无需扫码。
- Core 日志出现 `插件运行时启动失败: 等待 Runner 连接失败: Runner 进程已退出，退出码 1`（Runner 报缺少 `MAIBOT_IPC_ADDRESS`/`MAIBOT_SESSION_TOKEN`，上游缺陷，周期重试无法自愈）→ `docker-compose --env-file .env -f compose.yaml up -d --force-recreate core`。

恢复后在唯一白名单群发送一条消息并确认 MaiBot 回复，方为消息级闭环；2026-09-14 恢复后此项尚未完成。

## 可选公网管理入口

`public-maibot-admin` 默认不随 Core/NapCat 启动。若运营者明确接受明文 HTTP 风险，可填写私有 `.env` 中的 Caddy 与 Basic Auth 项，并执行：

```bash
./scripts/start-public-admin.sh
```

仅开放公网 TCP `8080`；不得开放 `18001`、`6081`、`6099`、`8120` 或 `3001`。Basic Auth 通过后仍须输入 MaiBot 原有 WebUI Token。NapCat 始终仅经 SSH 隧道管理。

## 尚待记录的验证证据

- 2026-09-14 恢复后的群内消息级收发（发送一条消息并确认回复）。
- Qwen-VL 对一张预先约定、无敏感信息且与问题同发的测试图片的实际处理结果。
- Qwen embedding 的实际 API 响应维度与 `.env` 声明的 `1024` 是否一致。
- 若启用公网管理代理，未授权访问的 `401`、二次 Token 校验以及内部端口未公开的检查结果。

这些是验证记录，不会改变当前服务范围。当前没有静态金融资料、资料索引、专用行情或交易能力，也没有外部告警；但新闻插件虽关闭，联网搜索插件已启用，不能保证回答不接触外部网页内容。
