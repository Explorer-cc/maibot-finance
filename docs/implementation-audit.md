# 第一版部署实现审计（更新至 2026-07-29）

## 结论

当前仓库已完成并通过真实验证的 **M0 最小闭环**：由忽略的 `.env` 生成私有运行配置，以固定镜像的 Compose 启动 MaiBot core 与 NapCat，并通过单群白名单、空私聊白名单、MCP 关闭、自身消息过滤和本机回环管理端口限制外部暴露。可选 `public-admin` 公网 IP HTTP 代理配置已加入仓库，但尚未在端口开放、密码或访问控制上完成部署验收；运营者已明确接受其明文传输风险。

2026-07-29 已完成真实 QQ 小号扫码登录，确认 NapCat 正向 WebSocket `3001` 启用，并在唯一 allowlist 群观察到 `QQ -> NapCat -> MaiBot -> DeepSeek -> QQ` 回复。运行态检查显示 Core health 为 `healthy`、Core/NapCat 重启次数均为 `0`，Core WebUI health 与 NapCat 本机管理面均可达。

M2 配置基线已完成：Core 配置加载 DeepSeek `deepseek-v4-flash`、Qwen-VL 和 Qwen embedding `text-embedding-v4`，A_Memorix 的查询、人物画像注入、群摘要和人物事实自动写回已开启，并通过 M2 预检。模型实际调用、资料导入、财经新闻 MCP 和外部告警均属于 M3 规划。

## 已核验

| 项目 | 结论 | 证据/位置 |
| --- | --- | --- |
| MaiBot 版本 | 合理，锁定 1.0.12 | 上游 tag 对应 commit `18f86829de6452b69f4eba14c38531678a585087`；配置版本为 bot `8.14.28`、model `1.17.6`。 |
| 镜像供应链 | 合理 | `.env.example` 固定 amd64 manifest digest，Compose 不使用 `latest`。 |
| 配置渲染 | 可用 | `deploy/bootstrap.py` 生成 `runtime/`，权限为私有；适配器 checkout 固定 commit `e34e286fa9c6f70e5c6aa3dc828451ab52c26773`。 |
| 渠道隔离 | 可用 | Adapter 为群 `whitelist`、仅一个群 ID、私聊白名单为空且 `ignore_self_message=true`。 |
| 网络暴露 | Core/NapCat/sqlite-web 合理；MaiBot 公网代理待验收 | WebUI、NapCat 和可选 sqlite-web 都保持 `127.0.0.1` 绑定；可选 `public-admin` profile 仅启动 Core 的 Caddy 代理，以公网 IP 的明文 HTTP `8080` 加 Basic Auth 对外代理。NapCat 不提供公网代理。 |
| 配置兼容性 | M0 已通过源码模型验证；M1 已通过真实运行配置预检与 Compose 部署；M2 预检已通过 | M0 已通过 MaiBot 1.0.12 的 Pydantic 配置模型与本地预检。M1 使用真实凭据渲染 DeepSeek + DashScope Qwen 配置，`./scripts/start.sh m1` 已通过预检并完成 Compose 重建。M2 复用当前配置基线，不包含额外 QQ 链路守卫。 |
| Python 工具环境 | 已建立 | 仓库 `.venv` 使用 Python 3.12.13，供 bootstrap、预检与上游模型校验使用。容器内 core 使用上游镜像自身的 Python 运行时。 |
| 容器启动 | M0 smoke test 与 M1 实际部署均已通过 | 假凭据 smoke test 中，锁定镜像的 `/api/webui/health` 返回 `healthy`，插件运行时加载且 A_Memorix 在 M0 保持关闭。2026-07-29 的 M1 部署后，Core 同样处于 `healthy`，NapCat 保持运行。 |
| 主机前置 | 已通过 | `scripts/host-check.sh` 已验证 Docker daemon、`docker-compose` 与 AppArmor parser；启动脚本会先执行该检查。 |
| 模型配置加载 | M0 与当前后端配置均已通过容器加载；模型调用结果待验证 | M0 加载结果：A_Memorix `false`、遥测 `false`、日志 `WARNING`、1 个模型。当前运行态加载 DeepSeek `deepseek-v4-flash`、Qwen-VL 和 Qwen embedding `text-embedding-v4`，并开启 A_Memorix 查询、人物画像注入和自动写回；尚未做 Qwen-VL 图片调用、embedding 端点响应或群内表情包行为验证。 |
| NapCat 容器 | 已通过启动验证 | 固定 `4.18.13` 镜像在回环管理端口返回 HTTP `301`；预置 `webui.json` 保持 `0600`，Docker logging driver 为 `none`。 |
| Core -> NapCat 网络 | 已通过真实验证 | 2026-07-29 完成 NapCat QQ 登录后，正向 WebSocket `3001` 启用，唯一 allowlist 群的真实消息成功经 Core 调用 DeepSeek 后回复。 |
| 原始 Compose M0 | 已通过端到端启动检查 | 使用假凭据运行未改写的 `compose.yaml`，core 进入 `healthy`、NapCat 启动、管理端口仅绑定回环，NapCat logging driver 为 `none`，core 日志未出现 WebUI token；测试服务随后已停止。 |
| 实际 M0 闭环 | 已通过 | 2026-07-29：真实凭据、QQ 扫码登录、正向 WebSocket `3001`、生产 allowlist 群回复均已验证；运行时 Core health=`healthy`，两个容器 restart count=`0`。 |

## 发现与微调

1. 上游当前存在 `1.1.0`，但本轮仍锁定 `1.0.12`。锁定版本比跟随最新版本更适合第一次接入；`plan.md` 已去除“1.1.0 不存在”的过时表述。
2. 当前后端保存 `talk_value=0.8`，但它只影响 MaiBot 的发言决策，不构成出站硬限流；本仓库不再部署外层 QQ 出站守卫。
3. M0 使用与后续阶段相同的已固定人格、但保持空知识库和关闭 A_Memorix。这样避免“最小人格”和实际启动配置不一致，同时仍保持 M0 范围最小。
4. 当前后端配置已同步到 `m1`/`m2` 生成器：加载 DeepSeek `deepseek-v4-flash`、Qwen-VL 与 Qwen embedding `text-embedding-v4`，并在唯一群通过 MaiBot 原生配置启用行为/表达/黑话学习（三者均 `use = true`、`learn = true`）、表情包收集（`steal_emoji = true`、`content_filtration = true`）、A_Memorix 查询、人物画像注入及人物事实/群摘要写回。部署层不新增媒体存储、清理、限额或回复逻辑。变更 embedding 模型或维度必须重建索引。
5. 锁定版默认会开启遥测，并在未配置 WebUI token 时把临时完整 token 输出到启动日志。部署生成器现要求单独的 `WEBUI_ACCESS_TOKEN`，预置为私有 `webui.json`，并关闭遥测、思考过程与模型请求/Prompt 快照。上游在读取自定义 token 时仍会输出其 8 字符前缀，因此 M0 将 core 日志级别限制为 `WARNING`；排障时如临时提高日志级别，必须避免将 Docker 日志外发或共享。
6. M3 的资料目录现在提供受控 manifest 与 SHA-256 校验器，但不包含任何金融资料，也不会自动导入。这样可以在运营者提供经许可文件后先校验元数据和文件完整性，再通过 WebUI 逐批导入。
7. NapCat 上游会把 WebUI token 与二维码写入 stdout。部署现在在首次启动前写入私有 `webui.json` 和正向 OneBot WebSocket `onebot11.json`（内部 `3001`、与适配器相同的 token），并禁用 NapCat 的 Docker 日志持久化；运营者只能经回环 WebUI + SSH 隧道完成登录，不能将容器日志作为登录通道。运行配置不再授予任何 QQ 身份插件权限。

## M3 金融知识库与财经新闻 MCP 仍未实现

- 在唯一 allowlist 群发送图片与问题在同一消息中的预先约定非敏感测试图片，记录 Qwen-VL 解析结果；引用旧消息中的图片不作为可靠的视觉输入验证。
- 记录 Qwen embedding 的实际端点响应和维度，核对其与已配置的 `text-embedding-v4` 及 `.env` 声明的 `1024` 一致。
- 验证 MaiBot 原生表情包收集行为，确认 `steal_emoji = true` 与 `content_filtration = true` 生效；不增加自定义媒体控制或回复逻辑。

- 登录失效、发送受限、重复事件等异常的外部可审计告警仍未实现。
- 为 `common` 与 `crypto` 资料完成 manifest 自动校验、导入、来源追溯和 scope/检索测试；不设置人工审核步骤。
- 确定并接入受限只读财经新闻 MCP，验证来源/发布时间/抓取时间标记、超时、频率和失败降级；不接入行情、交易或账户工具。

参见 `docs/open-items.md` 获取运营者必须提供或在外部控制台完成的项目。
