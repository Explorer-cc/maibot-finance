# 第一版部署实现审计（2026-07-28）

## 结论

当前仓库已具备 **M0 可接入部署工程**：由忽略的 `.env` 生成私有运行配置，以固定镜像的 Compose 启动 MaiBot core 与 NapCat，并通过单群白名单、空私聊白名单、MCP 关闭、自身消息过滤和本机回环管理端口限制外部暴露。

它还不是已完成的 M2，也不能声称已完成真实 QQ 消息往返：真实 QQ 登录、EULA/隐私确认和可用 DeepSeek 凭据均只应由运营者填入本机 `.env`。M2 的知识资料、视觉/embedding 凭据、知识导入与一周观察仍未执行。

## 已核验

| 项目 | 结论 | 证据/位置 |
| --- | --- | --- |
| MaiBot 版本 | 合理，锁定 1.0.12 | 上游 tag 对应 commit `18f86829de6452b69f4eba14c38531678a585087`；配置版本为 bot `8.14.28`、model `1.17.6`。 |
| 镜像供应链 | 合理 | `.env.example` 固定 amd64 manifest digest，Compose 不使用 `latest`。 |
| 配置渲染 | 可用 | `deploy/bootstrap.py` 生成 `runtime/`，权限为私有；适配器 checkout 固定 commit `e34e286fa9c6f70e5c6aa3dc828451ab52c26773`。 |
| 渠道隔离 | 可用 | Adapter 为群 `whitelist`、仅一个群 ID、私聊白名单为空且 `ignore_self_message=true`。 |
| 网络暴露 | 合理 | WebUI、NapCat 和可选 sqlite-web 都只绑定 `127.0.0.1`；sqlite-web 为只读的 `admin` profile。 |
| 配置兼容性 | 已通过源码模型验证 | M0/M2 渲染配置均已通过 MaiBot 1.0.12 的 Pydantic 配置模型与本地预检。 |
| Python 工具环境 | 已建立 | 仓库 `.venv` 使用 Python 3.12.13，供 bootstrap、预检与上游模型校验使用。容器内 core 使用上游镜像自身的 Python 运行时。 |
| 容器启动 | 已通过 core smoke test | 使用假凭据、回环端口启动锁定镜像，`/api/webui/health` 返回 `healthy`；插件运行时加载，A_Memorix 在 M0 正确保持关闭。 |
| 主机前置 | 已通过 | `scripts/host-check.sh` 已验证 Docker daemon、`docker-compose` 与 AppArmor parser；启动脚本会先执行该检查。 |
| M0/M2 配置加载 | 已通过容器实际模型校验 | M0 加载结果：A_Memorix `false`、遥测 `false`、日志 `WARNING`、1 个模型；M2：A_Memorix `true`、遥测 `false`、日志 `WARNING`、4 个模型。 |
| NapCat 容器 | 已通过启动验证 | 固定 `4.18.13` 镜像在回环管理端口返回 HTTP `301`；预置 `webui.json` 保持 `0600`，Docker logging driver 为 `none`。 |
| Core -> NapCat 网络 | 部分验证 | core 在同一 Docker 网络可解析 `napcat` 并对 `3001` 重连；未完成 QQ 登录时 NapCat 不监听 OneBot WebSocket，故无法在无账号测试中完成握手。 |
| 原始 Compose M0 | 已通过端到端启动检查 | 使用假凭据运行未改写的 `compose.yaml`，core 进入 `healthy`、NapCat 启动、管理端口仅绑定回环，NapCat logging driver 为 `none`，core 日志未出现 WebUI token；测试服务随后已停止。 |

## 发现与微调

1. 上游当前存在 `1.1.0`，但本轮仍锁定 `1.0.12`。锁定版本比跟随最新版本更适合第一次接入；`plan.md` 已去除“1.1.0 不存在”的过时表述。
2. 原计划把 `talk_value=0.75` 误当作可满足 5 QPM 的硬限流。源码核验表明它只控制发言频率；Adapter 提供重连、去重和白名单，但没有 per-group 出站 QPM 或连续回复冷却配置。因此精确限流已调整为 M2 前的明确实现缺口。
3. M0 使用与 M2 相同的已固定人格、但保持空知识库和关闭 A_Memorix。这样避免“最小人格”和实际启动配置不一致，同时仍保持 M0 范围最小。
4. 不启用 M2 的知识自动导入。锁定版有 A_Memorix 数据目录和 Web 导入配置，但在未提供经审核、具许可证资料前，自动导入会扩大范围且无法证明来源可追溯。M2 生成器已将豆包 embedding 模型接入 `model_task_config.embedding`，并把供应商确认的维度写入 `[a_memorix.embedding]`；变更模型或维度必须重建索引。
5. 锁定版默认会开启遥测，并在未配置 WebUI token 时把临时完整 token 输出到启动日志。部署生成器现要求单独的 `WEBUI_ACCESS_TOKEN`，预置为私有 `webui.json`，并关闭遥测、思考过程与模型请求/Prompt 快照。上游在读取自定义 token 时仍会输出其 8 字符前缀，因此 M0 将 core 日志级别限制为 `WARNING`；排障时如临时提高日志级别，必须避免将 Docker 日志外发或共享。
6. M2 的资料目录现在提供受控 manifest 与 SHA-256 校验器，但不包含任何金融资料，也不会自动导入。这样可以在运营者提供经许可文件后先校验元数据和文件完整性，再通过 WebUI 逐批导入。
7. NapCat 上游会把 WebUI token 与二维码写入 stdout。部署现在在首次启动前写入私有 `webui.json` 和正向 OneBot WebSocket `onebot11.json`（内部 `3001`、与适配器相同的 token），并禁用 NapCat 的 Docker 日志持久化；管理员只能经回环 WebUI 和 SSH 隧道完成登录，不能将容器日志作为登录通道。

## 尚未完成的接入验证

- 使用真实密钥验证 `QQ -> NapCat -> MaiBot -> DeepSeek -> QQ`。
- NapCat 扫码登录，并在其本机 WebUI 中核对预置的正向 WebSocket `3001` 已开始监听、token 未被改写。
- 在 M2 前增加并测试外层硬限流；随后才可满足计划中的 5 QPM/30 秒冷却要求。
- M2 的审核资料 manifest、导入、来源追溯和 scope/检索测试。

参见 `docs/open-items.md` 获取运营者必须提供或在外部控制台完成的项目。
