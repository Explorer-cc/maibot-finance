# 首次部署（M0）

本目录提供可实际启动的 M0 部署工程。运行期配置、密钥、QQ 登录态和数据均写入被 Git 忽略的 `runtime/`，不会进入仓库。

## 已完成的本机依赖

- Docker Engine 与 `docker-compose`
- AppArmor 与 `apparmor_parser`（Docker 在启用 AppArmor 的 Debian 上创建容器所需）
- Python 3.12 `.venv`（用于 bootstrap 与上游配置校验）

## 启动步骤

```bash
cp .env.example .env
# 编辑 .env，填写 docs/open-items.md 的 M0 项（包括独立的 WEBUI_ACCESS_TOKEN）
./scripts/start.sh m0
```

`bootstrap.py` 会将实际 `.env` 权限收紧为 `0600`；不要把它复制到 Git、工单、聊天记录或 WebUI 配置导出中。

先阅读锁定镜像中的 EULA 和隐私条款，再按 `.env.example` 的注释填入对应确认值。该值与 MaiBot 1.0.12 镜像内容绑定，不能用 `yes` 或任意文本代替。

`start.sh` 会先检查 Docker daemon、`docker-compose` 和 `apparmor_parser`。若缺少 AppArmor 工具，在 Debian 上安装：

```bash
sudo apt-get install apparmor apparmor-utils
```

启动后，WebUI 和 NapCat 管理面只绑定到服务器本机：

```bash
ssh -L 18001:127.0.0.1:18001 -L 6099:127.0.0.1:6099 <user>@<server>
```

然后访问本机 `http://127.0.0.1:6099` 完成扫码登录。bootstrap 已预置正向 WebSocket `3001` 和 `.env` 中的 `NAPCAT_WS_TOKEN`；登录后在 NapCat WebUI 中核对它仍为启用状态。完成后用生产群发送无敏感的 `@麦麦` 测试消息。

NapCat 的 WebUI 使用 `.env` 中的 `NAPCAT_WEBUI_TOKEN`。其上游会在 stdout 输出 token 和登录二维码，因此 Compose 默认禁用 NapCat 的 Docker 日志持久化；通过 WebUI 完成登录，不要依赖 `docker-compose logs napcat` 获取二维码。

## M2

在 `.env` 中补齐视觉与 embedding 项、审核 `common` 与 `crypto` 资料后，执行：

```bash
./scripts/start.sh m2
```

M2 不会开启实时行情、交易、MCP 或普通私聊。所有变更先运行：

```bash
.venv/bin/python scripts/preflight.py --phase m2 --compose
```

## 运维

```bash
./scripts/stop.sh
docker-compose --env-file .env -f compose.yaml logs -f core napcat
docker-compose --env-file .env -f compose.yaml --profile admin up -d sqlite-web
```

`sqlite-web` 是只读、按需启动的管理工具；不要把它暴露到公网。没有备份策略时，停止或重启服务不等于可以恢复运行期记忆和聊天数据。
