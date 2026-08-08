# 已有 MaiBot 实例的受控运维

本项目当前实例已完成升级并正常运行。日常操作以当前 `runtime/`、`.env` 和 Compose 容器为事实源；不要为日常启动重新执行 `deploy/bootstrap.py`，更不要使用 `--reset-config --yes-reset-config`。

## 当前服务与访问方式

- MaiBot WebUI：服务器 `127.0.0.1:18001`，本机 SSH 转发 `http://127.0.0.1:20003/`。
- NapCat WebUI：服务器 `127.0.0.1:6099`，本机 SSH 转发 `http://127.0.0.1:20002/`。
- Core、NapCat、可选 Caddy 管理代理由 `compose.yaml` 管理。
- SnowLuma 已预置为 `snowluma` profile，但当前不运行、不登录 QQ，也不接管 Core；其 Adapter 在维护窗口前不得安装到 Core 插件目录。

查看状态：

```bash
docker-compose --env-file .env -f compose.yaml ps
```

按当前配置启动或恢复 Core 与 NapCat：

```bash
docker-compose --env-file .env -f compose.yaml up -d core napcat
```

## SnowLuma 预置与首次登录

SnowLuma 只通过显式 profile 启动，且当前阶段不得停止或替换 NapCat：

```bash
docker-compose --env-file .env -f compose.yaml --profile snowluma up -d snowluma
```

这会仅绑定 SnowLuma WebUI 到服务器 `127.0.0.1:5099`。OneBot `3001` 不映射到主机，VNC `5900` 永不映射。首次生产 QQ 登录只能在维护窗口发生，届时才临时叠加 `compose.snowluma-login.yaml` 开放服务器回环 `6081`，并使用 SSH 转发访问 noVNC；登录确认后必须移除该覆盖文件启动的端口映射。

该命令使用现有 bind mount 的 `runtime/`，不会初始化或重置配置。启动后检查 Core 为 `healthy`，并在唯一 allowlist 群进行一次无敏感的消息收发确认。

## 私有运行配置

`runtime/` 与 `.env` 包含 Token、QQ 登录态、聊天记录和其他私有数据，均不得提交、复制到工单或公开。`bootstrap.py --initialize` 只能在缺失私有运行文件的新环境中使用；已有实例执行它不应用于重建或同步 WebUI 配置。

## 可选公网 HTTP 管理入口

`public-maibot-admin` 仅在运营者已接受明文 HTTP 风险时使用：

```bash
./scripts/start-public-admin.sh
```

它只代理 MaiBot 的 `8080` 管理入口，不公开 NapCat、`18001`、`6099`、`8120` 或 OneBot `3001`。公网入口启用后，仍保留 SSH 隧道作为受控管理入口。

## 只读管理与排障

```bash
docker-compose --env-file .env -f compose.yaml logs -f core napcat
docker-compose --env-file .env -f compose.yaml --profile admin up -d sqlite-web
```

`sqlite-web` 仅只读、按需启动，不得公开到公网。日志中可能含有敏感运行信息，排障输出不得外发。
