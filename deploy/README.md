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

逐项配置要求与外部控制台操作见 [`docs/open-items.md`](../docs/open-items.md)。除填写 M0 的 `.env` 项外，还必须生成三个彼此不同的 token：Core WebUI、NapCat WebUI 和 NapCat 正向 WebSocket。不配置 QQ 管理员身份或 QQ 维护命令；管理默认经 SSH 隧道，也可在运营者明确接受明文传输风险后使用可选公网 IP HTTP 代理。M2 不额外开启第二个群、普通私聊、MCP、实时数据或交易能力；M3 的财经新闻 MCP 另行设计与验收。

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

然后访问本机 `http://127.0.0.1:6099` 完成扫码登录。bootstrap 已预置唯一的正向 WebSocket `3001` 和 `.env` 中的 `NAPCAT_WS_TOKEN`；登录后在 NapCat WebUI 中核对它仍启用、token 未被改写且不回传自身消息。完成后只在生产群发送预先约定的无敏感 `@麦麦` 测试消息，记录 QQ 往返和 WebUI health 结果。

NapCat 的 WebUI 使用 `.env` 中的 `NAPCAT_WEBUI_TOKEN`。其上游会在 stdout 输出 token 和登录二维码，因此 Compose 默认禁用 NapCat 的 Docker 日志持久化；通过 WebUI 完成登录，不要依赖 `docker-compose logs napcat` 获取二维码。

## 可选：公网 IP 的两个 HTTP 管理入口（不安全例外）

在 `docs/open-items.md` 的“可选公网 IP HTTP 管理入口”全部前置条件完成后，填写 `.env` 中 `CADDY_IMAGE`、端口和 `*_ADMIN_*` 项，并执行：

```bash
./scripts/start-public-admin.sh
```

该命令仅启动 `public-maibot-admin` Caddy 容器，将 `http://<公网 IP>:8080` 代理至 Core。Basic Auth 通过后仍要输入 MaiBot 原有 token。NapCat 没有公网代理，必须经 SSH 隧道访问。此方案刻意禁用 HTTPS、不会申请证书；MaiBot 的公网链路会明文暴露用户名、密码和应用 token，运营者已明确接受该风险。

不要将 `18001`、`6099`、`8120` 或 `3001` 暴露到公网；Core、NapCat 和 sqlite-web 的 Compose 端口绑定必须保持 `127.0.0.1`。公网代理不会替代 SSH 隧道，SSH 仍作为代理或 DNS 故障时的受控应急入口。

## M1：模型与多模态就绪

当前后端配置基线已于 2026-07-29 同步到生成器：Core 健康加载 DeepSeek `deepseek-v4-flash`、Qwen-VL（`qwen3-vl-plus`）和 Qwen embedding（`text-embedding-v4`）。唯一群通过原生行为/表达/黑话学习与 `steal_emoji = true` 启用表情包收集，同时启用 A_Memorix 查询、人物画像注入、群摘要和人物事实自动写回；未导入金融资料或创建金融向量索引。

后续重建 M1 配置仍使用：

```bash
./scripts/start.sh m1
```

该命令加载 DeepSeek、Qwen-VL 与 Qwen embedding，并启用 MaiBot 原生行为/表达/黑话学习、表情包收集、A_Memorix 查询、人物画像注入、群摘要和人物事实自动写回；不会导入金融资料、创建金融向量索引或增加自定义媒体功能。

启动脚本会在生成配置后仅使用 Docker Compose 原生命令重建 `core`，让其读取新的模型配置；不会重启保持 QQ 登录态的 `napcat`。部署并不等同于验收：仍须在唯一 allowlist 群发送“图片与问题在同一消息中”的非敏感测试图片，核对图片理解、Qwen embedding 实际响应与 `.env` 声明的 1024 维，以及 MaiBot 原生表情包收集行为。引用旧消息中的图片不作为可靠的视觉输入验收方式。

## M2：配置与离线验收基线

M2 已完成配置基线：当前模型、人格、A_Memorix 与关闭引用回复已同步到生成器；使用 `scripts/preflight.py --phase m2` 检查配置一致性。

```bash
.venv/bin/python scripts/preflight.py --phase m2 --compose
```

`./scripts/start.sh m2` 会重建 Core，使其读取 M2 配置；不会重启 NapCat。

## M3：金融知识库与财经新闻 MCP（规划，未实现）

M3 拟验证模型实际调用和媒体行为；随后为 `common` 与 `crypto` 资料完成 manifest 自动校验、导入、可追溯检索、作用域隔离、故障降级与外部告警验证，并接入受限只读财经新闻 MCP。该 MCP 必须固定来源、返回来源与时间标记，且不提供行情、交易、账户、文件、Shell、Docker 或群管理能力。资料准入不要求人工审核。

## 运维

```bash
./scripts/stop.sh
docker-compose --env-file .env -f compose.yaml logs -f core napcat
docker-compose --env-file .env -f compose.yaml --profile admin up -d sqlite-web
```

`sqlite-web` 是只读、按需启动的管理工具；不要把它暴露到公网。没有备份策略时，停止或重启服务不等于可以恢复运行期记忆和聊天数据。
