# 部署未决项与人工操作

本文件是 `.env`、外部控制台和知识资料的配置清单。不得在此文件、提交记录、工单或聊天记录中填入密钥、群号、二维码、QQ 登录态或聊天正文。运行期值只写入被 Git 忽略且由 bootstrap 收紧为 `0600` 的 `.env` 与 `runtime/`。

## 先保持不变的模板值

`.env.example` 中的镜像 digest、适配器仓库/commit、默认 API base URL 与端口均已按 2026-07-28 的锁定实现核验。首次接入不应修改它们。

- 仅在本机端口冲突时修改 `WEBUI_PORT`、`NAPCAT_WEBUI_PORT` 或 `SQLITE_WEB_PORT`；保持 Compose 的 `127.0.0.1` 绑定。SSH 隧道始终可用；仅 MaiBot 管理入口可通过可选 `public-admin` profile 的 `8080` 公开，NapCat 管理面只经 SSH 隧道访问。
- 不将镜像改为 tag、`latest` 或未经审计的 digest；升级须重新核验 MaiBot 版本、镜像 digest、配置迁移与 Adapter 兼容性。
- 不在 M2 的 `.env` 中加入实时数据、交易、MCP、普通私聊或第二个群的配置；当前生成器会固定关闭/拒绝这些能力。M3 的财经新闻 MCP 另行设计，不提前写入模板。

## M0：必须填写的 `.env` 项

复制 `.env.example` 为忽略的 `.env`，将下表中所有值填写完毕后才可执行 `./scripts/start.sh m0`。QQ 号与群号必须为纯数字；模型 ID 必须以各供应商当日控制台或官方资料为准，不能只因模板给出默认值就视为可用。

| 类别 | `.env` 项 | 配置要求 |
| --- | --- | --- |
| 条款确认 | `MAIBOT_EULA_AGREE`、`MAIBOT_PRIVACY_AGREE` | 先阅读锁定 MaiBot 1.0.12 镜像内的条款，再填入 `.env.example` 注释中的精确确认值；镜像升级后重新确认。 |
| QQ 边界 | `BOT_QQ_ACCOUNT`、`PRODUCTION_GROUP_ID` | 分别填机器人小号与唯一允许的生产群。群白名单由 bootstrap 生成，私聊白名单固定为空；不配置 QQ 管理员、群角色或 QQ 维护命令。 |
| DeepSeek | `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL`、`DEEPSEEK_MODEL` | 填可实际调用的官方 API 凭据、端点和文本模型 ID；M0 的 QQ 往返依赖它。 |
| Core 管理面 | `WEBUI_ACCESS_TOKEN` | 独立随机值，至少 20 个字符；不得复用模型 key、QQ 密码或任何 NapCat token。 |
| NapCat 内部链路 | `NAPCAT_WS_TOKEN` | 独立随机值；建议至少 20 个字符。它同时写入 NapCat 正向 WebSocket `3001` 与 Adapter，不得与 WebUI token、模型 key 或 QQ 密码复用。 |
| NapCat 管理面 | `NAPCAT_WEBUI_TOKEN` | 独立随机值，至少 20 个字符；不得复用 core WebUI token、WS token、模型 key 或 QQ 密码。 |
| MaiBot 公网代理 | `CADDY_IMAGE`、`PUBLIC_HTTP_PORT`、`MAIBOT_ADMIN_USER`、`MAIBOT_ADMIN_PASSWORD_HASH` | 仅在启用 `public-admin` 时填写。密码项是 bcrypt 哈希，不是明文密码；此配置仅适用于已接受 HTTP 明文传输风险的运营者。NapCat 没有公网代理配置。 |

## 可选公网 IP HTTP 管理入口：上线前置条件与验收

此入口已获运营者授权，但默认不会随 `./scripts/start.sh` 启动。`public-maibot-admin` 仅公开 Caddy 的 `8080`（MaiBot），不改动 `core`、`napcat` 与 `sqlite-web` 的回环绑定，也不重启 QQ 链路。NapCat 管理面没有公网入口，必须使用 SSH 隧道。**MaiBot 公网入口不使用 HTTPS：Basic Auth 密码和 MaiBot token 将以明文经过公网；任意网络路径上的拦截者可接管 MaiBot 后台。**

1. 不需要域名或 DNS。确认服务器具有稳定公网 IPv4 地址。
2. 在服务器防火墙/云安全组开放 TCP `8080` 与既有 SSH 端口；不要开放 `18001`、`6099`、`8120` 或 `3001`。
3. 使用下列命令在可信终端生成两条**不同**的 bcrypt 哈希，并将原样输出填入 `.env` 的两个 `*_PASSWORD_HASH` 项。不要把明文密码、哈希或 `.env` 提交或发到聊天记录：

   ```bash
   docker run --rm caddy@sha256:4c6e91c6ed0e2fa03efd5b44747b625fec79bc9cd06ac5235a779726618e530d caddy hash-password --algorithm bcrypt --plaintext '<独立强密码>'
   ```

4. 填完 `.env` 后运行 `./scripts/start-public-admin.sh`。该脚本只拉取并启动/更新 `public-admin`，不会重启 Core 或 NapCat。
5. 验收 `http://<公网 IP>:8080`（MaiBot）：无 Basic Auth 返回 `401`；Basic Auth 通过后仍必须输入 MaiBot token。确认公网 IP 的 `18001`、`6099`、`8120`、`3001` 均不可达；NapCat 仅通过 SSH 隧道访问，并保留该隧道作为紧急管理入口。

## M0：必须完成的外部操作与验证

- [x] 已确认主机的 Docker daemon、`docker-compose`、AppArmor parser 与仓库 `.venv` 可用；`./scripts/start.sh m0` 已通过该检查（2026-07-29）。
- [x] 已确认机器人 QQ 小号在唯一生产群中，且能正常收发消息；白名单不会邀请、加入或服务其他会话（2026-07-29）。
- [x] 已经 SSH 隧道访问本机 NapCat WebUI，并按 QQ 正常流程扫码/验证登录；未绕过验证码、设备验证或其他平台安全校验（2026-07-29）。
- [x] 已核对 bootstrap 预置的正向 WebSocket 仅有一个，监听内部 `3001`，处于启用状态；未回传机器人自身消息（2026-07-29）。
- [x] 已在生产群以无敏感 `@麦麦` 触发样例确认 `QQ -> NapCat -> MaiBot -> DeepSeek -> QQ` 往返成功（2026-07-29）。跨群和私聊拒绝仍须按 `plan.md` 使用本地 fixture、受控测试路由或实现级测试验证，不新增真实会话。
- [x] 已保存不含密钥或聊天正文的验证证据：执行日期、锁定版本/digest、实际模型 ID、WebUI health 状态、QQ 往返结果与异常情况（2026-07-29；见 `docs/implementation-audit.md`）。

## M1：模型与多模态就绪配置与验收

M1 已在 M0 往返验证后部署。DashScope 凭据、工作空间 OpenAI 兼容端点与下列模型值已写入被忽略的 `.env`，不在本文件重复密钥或端点；模型 ID 和维度仍须以实际 API 响应完成验收。

| 类别 | `.env` 项 | 配置要求 |
| --- | --- | --- |
| Qwen-VL | `DASHSCOPE_API_KEY`、`DASHSCOPE_BASE_URL`、`QWEN_VL_MODEL` | 已配置 DashScope 工作空间 OpenAI 兼容端点和 `qwen3-vl-plus`；不得在文档中记录 key。 |
| Qwen embedding | `QWEN_EMBEDDING_MODEL`、`QWEN_EMBEDDING_DIMENSION` | 已配置 `text-embedding-v4`，`.env` 声明维度为 `1024`；须以实际返回核对维度。变更任一项前必须计划 A_Memorix 全量索引重建。 |

当前后端配置的剩余验收需要一张预先约定、无敏感信息且允许发送给模型的测试图片。将图片与问题附在同一条群消息中，验证 Qwen-VL 解析，并记录 Qwen embedding 的模型 ID 与实际响应维度；引用旧消息中的图片不是可靠的视觉输入验证。唯一 allowlist 群已启用 MaiBot 原生行为/表达/黑话学习与表情包收集；三类学习均 `use = true`、`learn = true`，`steal_emoji = true` 并保持 `content_filtration = true`，且 `enable_rich_reply = true` 只使用 MaiBot 既有的图片、表情包和 @ 附加能力。A_Memorix 查询、人物画像注入、群摘要和人物事实自动写回也已启用；仍不导入金融资料或创建金融向量索引。

**当前状态：** 后端保存的配置已同步到 `deploy/bootstrap.py` 与 `scripts/preflight.py`；Core 健康加载 DeepSeek `deepseek-v4-flash`、Qwen-VL 与 Qwen embedding，并在唯一群通过 MaiBot 原生行为/表达/黑话学习和 `steal_emoji` 启用表情包收集，同时启用 A_Memorix 插件、检索工具、人物画像注入和人物事实/群摘要写回。真实图片、embedding 和表情包链路测试仍待执行。

## M2：配置与离线验收（已完成）

M2 复用当前 DashScope Qwen embedding 配置；运行 `./scripts/start.sh m2` 会重建 Core，使其读取 M2 配置，但不会重启 NapCat。

M2 没有新的模型 `.env` 项：复用当前的 `QWEN_EMBEDDING_MODEL` 与 `QWEN_EMBEDDING_DIMENSION`。

| 类别 | 位置 | 配置要求 |
| --- | --- | --- |
| 静态知识 | `knowledge/` 中的资料与相邻 manifest | M3 资料与 manifest 须通过来源 HTTPS、许可证、允许域、日期和 SHA-256 自动校验；不得导入群消息、模型输出、实时行情或未经许可的抓取内容。 |

## M3：金融知识库与财经新闻 MCP 所需输入（未实现）

以下项目不随 M2 配置基线完成，属于 M3 的金融知识库与财经新闻 MCP 规划：

- [ ] 验证 Qwen-VL、Qwen embedding 与表情包收集的真实响应；核对 embedding 实际维度。
- [ ] 提供 `common` 与 `crypto` 资料及相邻 manifest；每份资料通过 `scripts/validate_knowledge_manifest.py` 后导入并验证来源追溯、召回、基础作用域隔离、无实时行情声明和当前激进金融人格一致性。
- [ ] 确定财经新闻 MCP 的固定来源、授权/使用条款、只读新闻查询范围、鉴权方式、速率/超时和来源时间字段；不得提供行情、交易或账户功能。
- [ ] 接入登录失效、频繁验证和平台冻结的外部可审计告警，并验证最小处置卡。

## 已核验的实现事实（2026-07-28）

- MaiBot 源码 tag `1.0.12` 指向 `18f86829de6452b69f4eba14c38531678a585087`，Dockerfile 使用 Python 3.13；源码本地校验最低要求为 Python 3.12。
- 固定镜像（amd64）：`sengokucola/maibot@sha256:cceee3284a03eef34105a1855155e882ab36325fda03dd101000c6f4b26e165e`（tag `1.0.12`）、`mlikiowa/napcat-docker@sha256:11d72e50b6edc01b20f1a7611a250720e61412fe96184e3c70c3b8cf976744e1`（tag `v4.18.13`）和 `coleifer/sqlite-web@sha256:1e5b86237968ed747554f951c6df2fc2fe4bf4ef070b8ca23d553d7f6c6426f7`。
- MaiBot `1.0.12` 的配置版本为 `bot_config=8.14.28`、`model_config=1.17.6`；NapCat Adapter 当前核验提交为 `e34e286fa9c6f70e5c6aa3dc828451ab52c26773`，插件配置版本为 `0.1.0`。
- 适配器使用正向 WebSocket，默认端口 `3001`，并原生支持群/私聊 whitelist；本部署仅设置一个群 whitelist 且私聊列表为空。
- 上游仓库目前也可见 tag `1.1.0`。本项目仍按已确认范围锁定 `1.0.12`，不会自动升级；后续升级必须重新审计镜像 digest、配置迁移和适配器兼容性。
