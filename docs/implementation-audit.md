# 当前部署实现审计（更新至 2026-09-14）

## 结论

当前实例运行 MaiBot `1.2.3`，内置 WebUI `1.7.2`；Core 为 `healthy`，SnowLuma 是唯一运行中的 QQ 网关。2026-08-24 升级执行了 `vector → vector_intent` 配置迁移，数据库、A_Memorix 记忆、聊天记录与表情目录未重置，升级后的 SQLite `quick_check` 通过。2026-09-14 凌晨发生约 50 分钟消息链路中断（QQ 登录就绪探测失败 + 插件运行时启动缺陷叠加），已通过重启 SnowLuma 与强制重建 Core 恢复至登录、OneBot 监听、适配器连接与插件加载；恢复后群内消息级收发待重新核验。事件详情见下方「运维事件记录」。

| 项目 | 当前事实 |
| --- | --- |
| MaiBot | `1.2.3`；内置 WebUI `1.7.2`；镜像 digest 由私有 `.env` 锁定；Core schema `40` |
| SnowLuma | `v1.14.3`；WebUI 绑定服务器 `127.0.0.1:5099`，noVNC 固定绑定 `127.0.0.1:6081`；OneBot `3001` 仅限 Compose 私有网络 |
| Adapter | MaiBot-SnowLuma-Adapter `403de73785d1755a9a6b9828e403ed30399b638d` 已启用；NapCat Adapter 已禁用 |
| NapCat | `v4.18.18` 容器已从 Docker 移除（`docker ps -a` 无此容器）；`runtime/napcat-config/` 与 `runtime/backups/` 回滚资料保留 |
| Core 管理面 | `127.0.0.1:18001`；本地 SSH 转发为 `20003` |
| 模型 | 已登记 `商汤deepseek`、`基元律动`、`基元律动2`、`DashScope`、`tokneflux`（无模型）、`gemini` 六个提供商；各任务候选以 `gemini-3.8/3.7-flash` 开头（策略 `balance`），回退到商汤/基元律动 deepseek、GLM、qwen、minimax 系列，视觉另含 `sensenova-6.8-flash-lite`，embedding 为 `text-embedding-v4`。`gemini` Key 无效（401），任务经回退链完成，回复未中断；embedding 维度未核验 |
| 记忆与学习 | A_Memorix 查询、人物画像注入、群摘要/事实写回、行为/表达/黑话学习和表情包收集均已开启；富回复关闭，表情包内容过滤关闭 |
| 渠道隔离 | 单群白名单、私聊白名单为空、自身消息过滤开启 |
| MCP 与工具 | MCP 关闭；没有专用行情或交易插件，但存在联网搜索、图片下载、EXIF 定位、群聊分析和第三方 Python 插件 |
| 公网管理面 | `public-maibot-admin` 当前未运行；其 Caddy 配置若启动将公开 `0.0.0.0:8080`，使用 Basic Auth 但没有 HTTPS |

## 插件审计

| 插件 | 配置状态 | 实际作用与审计结论 |
| --- | --- | --- |
| SnowLuma Adapter | 启用 | 当前 QQ 连接必需；群白名单、私聊空白名单和自身消息过滤均已配置。 |
| NapCat Adapter | 禁用 | 旧 QQ 接入保留用于回滚；不得与 SnowLuma 同时登录生产账号。 |
| 智能戳一戳 | 启用 | 可在群聊与私聊响应，并允许主动戳一戳；作用域未在插件自身再次收窄。私聊目前由 Adapter 阻断。 |
| 内部回复再审、语义闭环 | 启用 | 修改内部回复决策或发送流程；未发现外部网络能力，但未做行为回归验收。 |
| Pixiv 图片 | 启用 | 从外部 API 下载图片；聊天过滤关闭。色图群白名单为空，但私聊策略允许色图。 |
| 照片 EXIF 定位 | 启用 | 读取图片/文件 GPS，调用 OSM 或高德并在群内回复地址；会记录坐标与地址，存在显著隐私和日志泄露风险。 |
| 每日群聊分析 | 启用 | 每日自动汇总所有可见活跃群；日志证明已对唯一群发起 LLM 总结，曾超时或得到空结果。 |
| 联网搜索 | 启用 | 允许外部网页搜索与内容抓取；并非专用行情工具，但会引入未经资料治理的外部内容。 |
| 每日新闻、绘图、鹿管、Emoji 文本选择 | 关闭 | 已安装但其各自配置开关为关闭；仍应视为可被后续启用的第三方代码。 |

## 运维事件记录

### 2026-09-14 消息链路中断与恢复

| 时间（本地） | 事件 |
| --- | --- |
| 00:35 | SnowLuma 已现异常前兆：`[Hook] process enumeration timed out`、`[OneBot.GroupRequests] group request scan failed`。 |
| 00:48 | 双容器同时重启（容器为 2026-08-25 创建，属 restart 非重建）。 |
| 00:52 | Core：IPC 插件运行时启动失败，Runner 进程以“缺少必要的环境变量: MAIBOT_IPC_ADDRESS, MAIBOT_SESSION_TOKEN”退出（退出码 1），supervisor 周期重试均失败，全部第三方插件未加载；SnowLuma：`[Hook] load failed: PID=64 COMPONENT_LOAD_FAILED`。 |
| 00:54–01:26 | QQ 停留在 `login identity discovered; awaiting readiness`，`[LoginProbe] login check timed out`（部署以来首次），OneBot `3001` 从未监听。 |
| 01:35 | `docker restart maibot-snowluma` → 30 秒内 `login detected`，OneBot HTTP `3000` 与 WS `3001` 监听，8 群 6060 成员加载。 |
| 01:37 | `docker-compose --env-file .env -f compose.yaml up -d --force-recreate core` → 插件 Runner 存活、IPC socket 连接、适配器回连 `snowluma:3001`，healthcheck `healthy`，日志零错误。 |

核验结论：SnowLuma Hook 注入失败为偶发，重启容器重试即可恢复，无需扫码；MaiBot `1.2.3` 插件 Runner 环境变量缺失为上游缺陷（容器存续期约 490 次进程启动中出现 8 次），重启进程无效，需强制重建容器；Core 健康检查仅探测 WebUI `8001`，故障期间仍报 `healthy`。恢复后群内消息级收发尚未重新核验。

### 运行观察（2026-09-13/14）

- MaiBot 进程内置看门狗在 LLM 硬错误后自愈重启 bot.py（entrypoint 无重启循环，容器 `RestartCount` 不体现），活跃期约每 10 分钟一次；gemini 401 硬错误为主要诱因之一。
- 语音消息（Silk）因 Core 容器无 ffmpeg 转码失败，多次降级为文本占位（2026-09-12 日志）。
- SnowLuma 内 QQ hotUpdate 检查持续失败（更新域名解析被指向 `0.0.0.0`，`ECONNREFUSED 0.0.0.0:443`），不影响 QQ 主连接与消息收发，但持续产生错误日志。

## 已知限制

- Core 健康检查仅探测 WebUI HTTP 接口，不覆盖 IPC 插件运行时与适配器连通性；`healthy` 不代表消息链路可用（2026-09-14 故障证实）。
- MaiBot `1.2.3` 插件运行时存在偶发 Runner 启动缺陷（环境变量缺失、上游问题），全部第三方插件不加载且无法自愈，需 `--force-recreate` 重建 Core。
- SnowLuma Hook 组件注入偶发失败会阻断 QQ 登录就绪探测与 OneBot 启动；`docker restart maibot-snowluma` 可恢复。
- 旧表情/GIF、文件及特殊 OneBot 消息段尚未完成迁移后 QQ 验证；语音消息因 Core 容器无 ffmpeg 降级为文本占位，正常语音输出未核验。
- Qwen-VL 的真实图片调用结果和 Qwen embedding 的实际响应维度尚未记录为验收证据。
- 当前没有已导入的静态金融资料或金融资料索引。
- 没有外部告警系统；容器状态与 QQ 连接需由运营者通过受控管理入口检查。
- 维护窗口生成了一份私有回滚备份；稳定观察完成并经运营者确认精确目标前不得删除，且不得承诺其能恢复未验证的数据。
- `public-maibot-admin` 当前未运行；若启动，用户名、密码和应用 Token 可能在公网 HTTP 链路暴露。
- Core 的 `plugin.permission` 含有 QQ 标识；其权限语义尚未按上游文档核验。
- Core 以读写方式挂载整个插件目录。所有启用的第三方插件都在 Core 容器权限范围内运行，可读取可见聊天、访问网络，并可能接触运行配置；没有沙箱隔离。

## 变更约束

升级前应记录镜像 digest、Adapter commit、配置迁移说明和验证结果。2026-08-24 已使用锁定 digest `sha256:79bb84671a617ba11327c910f847348490573e39bc06f50a528e2b1ca185d129` 升级 MaiBot Core/WebUI，并在 `runtime/backups/upgrade-before-20260824-015139/` 保留通过 SHA-256 校验的私有回滚备份。不要以 `latest` 更新镜像；不要通过 `--reset-config --yes-reset-config` 覆盖已有 `runtime/`，除非运营者明确要求恢复操作。
