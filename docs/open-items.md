# 部署未决项与人工操作

本文件是 `.env`、外部控制台和知识资料的配置清单。不得在此文件、提交记录、工单或聊天记录中填入密钥、群号、二维码、QQ 登录态或聊天正文。运行期值只写入被 Git 忽略且由 bootstrap 收紧为 `0600` 的 `.env` 与 `runtime/`。

## 先保持不变的模板值

`.env.example` 中的镜像 digest、适配器仓库/commit、默认 API base URL 与端口均已按 2026-07-28 的锁定实现核验。首次接入不应修改它们。

- 仅在本机端口冲突时修改 `WEBUI_PORT`、`NAPCAT_WEBUI_PORT` 或 `SQLITE_WEB_PORT`；保持 Compose 的 `127.0.0.1` 绑定，并同步调整 SSH 隧道命令。
- 不将镜像改为 tag、`latest` 或未经审计的 digest；升级须重新核验 MaiBot 版本、镜像 digest、配置迁移与 Adapter 兼容性。
- 不在 `.env` 中加入实时数据、交易、MCP、普通私聊或第二个群的配置；当前生成器会固定关闭/拒绝这些能力。

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

## M0：必须完成的外部操作与验证

- [x] 已确认主机的 Docker daemon、`docker-compose`、AppArmor parser 与仓库 `.venv` 可用；`./scripts/start.sh m0` 已通过该检查（2026-07-29）。
- [x] 已确认机器人 QQ 小号在唯一生产群中，且能正常收发消息；白名单不会邀请、加入或服务其他会话（2026-07-29）。
- [x] 已经 SSH 隧道访问本机 NapCat WebUI，并按 QQ 正常流程扫码/验证登录；未绕过验证码、设备验证或其他平台安全校验（2026-07-29）。
- [x] 已核对 bootstrap 预置的正向 WebSocket 仅有一个，监听内部 `3001`，处于启用状态；未回传机器人自身消息（2026-07-29）。
- [x] 已在生产群以无敏感 `@麦麦` 触发样例确认 `QQ -> NapCat -> MaiBot -> DeepSeek -> QQ` 往返成功（2026-07-29）。跨群和私聊拒绝仍须按 `plan.md` 使用本地 fixture、受控测试路由或实现级测试验证，不新增真实会话。
- [x] 已保存不含密钥或聊天正文的验证证据：执行日期、锁定版本/digest、实际模型 ID、WebUI health 状态、QQ 往返结果与异常情况（2026-07-29；见 `docs/implementation-audit.md`）。

## M1：模型与多模态就绪所需配置

M1 在 M0 往返验证通过后进行。先在供应商控制台或官方文档确认下列模型项；模型 ID 与 embedding 维度不能只因模板给出候选值而视为已验证。

| 类别 | `.env` 项 | 配置要求 |
| --- | --- | --- |
| Qwen-VL | `DASHSCOPE_API_KEY`、`DASHSCOPE_BASE_URL`、`QWEN_VL_MODEL` | 填 DashScope 官方兼容端点、可用 key 和实际 Qwen-VL 模型 ID。 |
| 豆包视觉 | `VOLCENGINE_API_KEY`、`VOLCENGINE_BASE_URL`、`DOUBAO_VISION_MODEL` | 填火山方舟官方端点、可用 key 和实际视觉模型 ID；作为 Qwen-VL 的顺序降级项。 |
| 豆包 embedding | `DOUBAO_EMBEDDING_MODEL`、`DOUBAO_EMBEDDING_DIMENSION` | 将模型 ID 与供应商实际返回/官方资料确认的维度成对填写。模板的 `doubao-embedding-vision` 与 `1024` 只是当前候选，不能未经确认上线。模型或维度变更前必须计划 A_Memorix 全量索引重建。 |

M1 的验收还需要一张预先约定、无敏感信息且允许发送给模型的测试图片，验证 Qwen-VL 主用、豆包视觉顺序回退和失败降级。M1 不导入金融资料、不创建金融向量索引，也不因测试 embedding 自动写入群摘要或人物事实。

**当前实现：** `scripts/start.sh m1`、`deploy/bootstrap.py --phase m1` 和 `scripts/preflight.py --phase m1` 已可用。M1 生成器加载视觉与 embedding 模型，但保持 A_Memorix 插件、检索工具和人物画像注入关闭；可用 M1 进行模型和图片链路测试，不必运行 `m2`。

## M2：静态金融知识与检索所需资料

M2 以已完成的 M1 为前提。仅导入 `common` 与 `crypto` 机制科普资料；每份文件须通过 `scripts/validate_knowledge_manifest.py`，再由运营者经 SSH 隧道后的 WebUI 导入并记录来源召回验证。资料准入不要求人工审核。

M2 **没有新的 `.env` 项**：它复用 M0 的渠道/DeepSeek 配置和 M1 的视觉/embedding 配置。真实 `.env` 中已有的值无需移动、重新生成或修改；M2 的新增输入是 `knowledge/` 下的资料和 manifest。

| 类别 | 位置 | 配置要求 |
| --- | --- | --- |
| 静态知识 | `knowledge/` 中的资料与相邻 manifest | 资料与 manifest 须通过来源 HTTPS、许可证、允许域、日期和 SHA-256 自动校验；不得导入群消息、模型输出、实时行情或未经许可的抓取内容。 |

## M2：当前不能靠填写 `.env` 完成的门槛

以下项目不是现有 MaiBot 1.0.12 或 Adapter 的环境变量，也尚未由仓库实现；在补齐并验收前，不能把 M2 视为完成：

- [ ] 受控的外层出站硬限流：唯一生产群每分钟最多 5 条，连续 3 条后强制冷却 30 秒。`talk_value=0.75`、`max_consecutive_wait_count` 与空闲退避只影响回复决策，不能替代硬限流。
- [ ] 运营者可仅经 SSH 隧道后的 WebUI token 执行暂停 QQ 入站/出站、关闭主动发言和紧急停机，并验证不会删除运行期数据；群聊消息不能触发这些操作。
- [ ] 登录失效、频繁验证、发送受限、冻结提示、重复事件和 Adapter 异常的可审计告警与最小处置卡。
- [ ] `common` 与 `crypto` 的来源追溯、召回、基础作用域隔离、无实时行情声明和高风险金融请求拒绝测试。

## 已核验的实现事实（2026-07-28）

- MaiBot 源码 tag `1.0.12` 指向 `18f86829de6452b69f4eba14c38531678a585087`，Dockerfile 使用 Python 3.13；源码本地校验最低要求为 Python 3.12。
- 固定镜像（amd64）：`sengokucola/maibot@sha256:cceee3284a03eef34105a1855155e882ab36325fda03dd101000c6f4b26e165e`（tag `1.0.12`）、`mlikiowa/napcat-docker@sha256:11d72e50b6edc01b20f1a7611a250720e61412fe96184e3c70c3b8cf976744e1`（tag `v4.18.13`）和 `coleifer/sqlite-web@sha256:1e5b86237968ed747554f951c6df2fc2fe4bf4ef070b8ca23d553d7f6c6426f7`。
- MaiBot `1.0.12` 的配置版本为 `bot_config=8.14.28`、`model_config=1.17.6`；NapCat Adapter 当前核验提交为 `e34e286fa9c6f70e5c6aa3dc828451ab52c26773`，插件配置版本为 `0.1.0`。
- 适配器使用正向 WebSocket，默认端口 `3001`，并原生支持群/私聊 whitelist；本部署仅设置一个群 whitelist 且私聊列表为空。
- 上游仓库目前也可见 tag `1.1.0`。本项目仍按已确认范围锁定 `1.0.12`，不会自动升级；后续升级必须重新审计镜像 digest、配置迁移和适配器兼容性。
