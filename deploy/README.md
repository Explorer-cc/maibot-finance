# 已有 MaiBot 实例的受控运维

本项目当前实例已完成升级并正常运行。日常操作以当前 `runtime/`、`.env` 和 Compose 容器为事实源；不要为日常启动重新执行 `deploy/bootstrap.py`，更不要使用 `--reset-config --yes-reset-config`。

## 当前服务与访问方式

- MaiBot Core `1.2.3` / WebUI `1.7.2`：服务器 `127.0.0.1:18001`，本机 SSH 转发 `http://127.0.0.1:20003/`。
- NapCat `v4.18.18` WebUI：服务器 `127.0.0.1:6099`，本机 SSH 转发 `http://127.0.0.1:20002/`；NapCat 当前停止，仅保留回滚资料。
- Core、NapCat、SnowLuma 与可选 Caddy 管理代理由 `compose.yaml` 管理。
- SnowLuma `v1.14.3` 当前运行并接管 QQ；其 Adapter 使用固定提交 `403de73785d1755a9a6b9828e403ed30399b638d`。

查看状态：

```bash
docker-compose --env-file .env -f compose.yaml ps
```

按当前配置启动或恢复 Core 与 SnowLuma（显式服务名，绝不拉起 NapCat）：

```bash
docker-compose --env-file .env -f compose.yaml --profile snowluma up -d core snowluma
```

## SnowLuma 预置与首次登录

SnowLuma 通过显式 `snowluma` profile 启动；当前生产接入由 SnowLuma 接管，NapCat 保持停止，仅用于回滚：

```bash
docker-compose --env-file .env -f compose.yaml --profile snowluma up -d snowluma
```

这会绑定 SnowLuma WebUI 到服务器 `127.0.0.1:5099`，并保留 noVNC 回环映射 `127.0.0.1:6081`，可经本机或 SSH 隧道维护。OneBot `3001` 不映射到主机，VNC `5900` 永不映射；不得将 noVNC 映射到公网地址。`compose.snowluma-login.yaml` 是历史兼容覆盖文件，不再用于改变 noVNC 端口暴露。

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
docker-compose --env-file .env -f compose.yaml logs -f core snowluma
docker-compose --env-file .env -f compose.yaml --profile admin up -d sqlite-web
```

`sqlite-web` 仅只读、按需启动，不得公开到公网。日志中可能含有敏感运行信息，排障输出不得外发。
