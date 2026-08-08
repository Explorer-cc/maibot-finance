# 当前运行事项与私有配置说明

本文件说明已有实例的配置边界和仍需记录的验证事实。不得在本文件、提交记录、工单或聊天记录中填入密钥、群号、二维码、QQ 登录态或聊天正文。

## 当前已固定的私有配置

- `.env` 中锁定 MaiBot、NapCat、sqlite-web 与 Caddy 的镜像 digest；不得改为 tag 或 `latest`。
- Core WebUI、NapCat WebUI 与 sqlite-web 保持服务器回环绑定；既有 SSH 转发保持不变。
- 唯一生产群、WebUI Token、NapCat WebUI Token 和内部 WebSocket Token 均为私有值，不得复用或外泄。
- DeepSeek 与 DashScope 凭据只保存在 `.env`；模型名称和 embedding 配置以当前运行值为准。
- Adapter 当前拒绝普通私聊和第二个群，MCP 保持关闭；但已启用联网搜索、外部图片下载、EXIF 定位和群聊分析插件。不要将本实例描述为没有联网或外部工具。

## 日常操作

查看状态：

```bash
docker-compose --env-file .env -f compose.yaml ps
```

确认 Core 与 NapCat 已启动：

```bash
docker-compose --env-file .env -f compose.yaml up -d core napcat
```

这两个命令使用现有 `runtime/`，不重置配置。不要为日常运维运行 `deploy/bootstrap.py`，也不要执行 `--reset-config --yes-reset-config`。

## 可选公网管理入口

`public-maibot-admin` 默认不随 Core/NapCat 启动。若运营者明确接受明文 HTTP 风险，可填写私有 `.env` 中的 Caddy 与 Basic Auth 项，并执行：

```bash
./scripts/start-public-admin.sh
```

仅开放公网 TCP `8080`；不得开放 `18001`、`6099`、`8120` 或 `3001`。Basic Auth 通过后仍须输入 MaiBot 原有 WebUI Token。NapCat 始终仅经 SSH 隧道管理。

## 尚待记录的验证证据

- Qwen-VL 对一张预先约定、无敏感信息且与问题同发的测试图片的实际处理结果。
- Qwen embedding 的实际 API 响应维度与 `.env` 声明的 `1024` 是否一致。
- 若启用公网管理代理，未授权访问的 `401`、二次 Token 校验以及内部端口未公开的检查结果。

这些是验证记录，不会改变当前服务范围。当前没有静态金融资料、资料索引、专用行情或交易能力，也没有外部告警；但新闻插件虽关闭，联网搜索插件已启用，不能保证回答不接触外部网页内容。
