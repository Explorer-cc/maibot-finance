# MaiBot 私有 QQ 群聊人格助手 PRD

## 当前运行定义

麦麦（MaiSaka）是运行在一个受邀私有 QQ 群内的 MaiBot 人格实例。她会参与日常聊天；在金融话题中保持当前配置的激进投资损友风格，但不是公开金融服务、实时市场服务或交易系统。

本仓库是部署配置与文档仓库。当前运行事实来自私有 `.env`、`runtime/` 与容器，而不是本文件。

## 运行状态

| 组件 | 当前状态 |
| --- | --- |
| MaiBot Core | `1.2.3`，内置 WebUI `1.7.2`，`maibot-core` 为 `healthy`；Core schema `40`，升级执行了 `vector → vector_intent` 配置迁移，未重置既有数据 |
| SnowLuma | `v1.14.3`，`maibot-snowluma` 正在运行；WebUI 绑定 `127.0.0.1:5099`，noVNC 固定绑定 `127.0.0.1:6081` |
| Adapter | MaiBot-SnowLuma-Adapter `403de73785d1755a9a6b9828e403ed30399b638d` 已启用；NapCat Adapter 已禁用 |
| NapCat | `v4.18.18`，容器已从 Docker 移除；`runtime/napcat-config/` 与 `runtime/backups/` 回滚资料保留 |
| 管理代理 | `public-maibot-admin` 当前未运行；配置保留，启动后公网监听 HTTP `8080` |
| Core WebUI | 服务器 `127.0.0.1:18001`；SSH 本机转发 `20003` |
| SnowLuma WebUI | 服务器 `127.0.0.1:5099`；SSH 本机转发 `20004` |

唯一白名单群的 SnowLuma 入站文本与 MaiBot 出站回复已经验证。Core 继续使用原数据库、记忆、聊天记录和表情目录；旧表情/GIF、文件与特殊消息段尚未核验；语音消息经 2026-09-12 日志证实因 Core 容器无 ffmpeg 降级为文本占位。2026-09-14 凌晨消息链路故障约 50 分钟后已恢复（详见 `docs/implementation-audit.md` 运维事件记录），恢复后群内消息级收发待重新核验。

## 当前功能边界

### QQ 与群聊

- Adapter 使用群白名单，当前仅包含一个 QQ 群；私聊白名单为空。
- Adapter 启用自身消息过滤。
- 群聊主动发言参数为 `talk_value = 0.75`（2026-10-01 自 `0.95` 下调，用于降低 OOM 高活跃期的堆增长速率）；私聊为 `0`；被 @ 时尽量回复。
- 引用回复和富回复都关闭。群聊可使用原生图片处理与表情包收集；表情包内容过滤当前关闭。
- 人格是运行配置中“对金融投资略微感兴趣、偏好激进策略、日常话题不强行带入投资”的群友；当前没有仓库内的人格文本作为运行来源。

### 记忆与学习

- A_Memorix、记忆查询、人物画像查询与注入、群摘要写回、人物事实写回均开启。
- 行为学习、表达学习与黑话学习仅作用于已配置的唯一群。
- 普通记忆全局共享与启发式跨聊天召回均关闭。
- 当前没有已导入的静态金融资料，也没有金融资料索引。

### 插件与外部数据处理

- SnowLuma Adapter 是当前 QQ 渠道所必需的已启用适配器；NapCat Adapter 保留但禁用。
- 智能戳一戳、内部回复再审、Pixiv 图片、照片 EXIF 定位、每日群聊分析和联网搜索插件均在各自配置中启用。每日群聊分析已有实际 LLM 调用日志，虽曾出现超时和空结果。
- 联网搜索插件启用网页内容抓取及多个搜索后端；它不是专用行情工具，但可以获得不受资料库约束的外部网页内容。
- 照片定位插件读取群内图片和文件的 EXIF GPS，向 OSM 或高德逆地理编码服务发送坐标，并在群内 @ 发图人显示地址。它会在 Core 日志中记录坐标和地址。
- Pixiv 图片插件启用外部图片下载；其聊天过滤关闭，色图策略使用群白名单但名单为空，私聊策略允许色图。当前 Adapter 私聊白名单为空，仍阻断普通私聊事件。
- 每日群聊分析插件启用每日自动总结；空目标群列表按插件实现表示所有活跃群。当前它只会看到 Adapter 白名单内的群，但没有插件自身的单群限制。
- 每日新闻、绘图、鹿管记录和 Emoji 文本选择插件已安装但其配置开关为关闭。

### 模型配置

当前 `model_config.toml` 登记六个 API 提供商：`商汤deepseek`、`基元律动`、`基元律动2`、`DashScope`、`tokneflux`（未挂任何模型）与 `gemini`（`client_type = "gemini"`）。原 DeepSeek、LLMX、ZhipuAI 提供商已不在当前配置中。

除留空任务外，各任务候选列表均以 `gemini-3.8-flash` 与 `gemini-3.7-flash` 开头，选择策略为 `balance`：

| 任务 | 当前候选模型 |
| --- | --- |
| 回复（replyer） | `gemini-3.8/3.7-flash`、基元律动 `deepseek-v4-flash-0731`/`glm-5.3-flash`/`deepseek-v4-pro`、基元律动2 `deepseek-v4-flash`/`deepseek-v4-pro`/`GLM-5.2`/`minimax-m2.7` |
| 规划（planner） | `gemini-3.8/3.7-flash`、基元律动 `deepseek-v4-pro`/`deepseek-v4-flash-0731`/`glm-5.3-flash`、商汤 `glm-5.2`、基元律动2 `deepseek-v4-flash`/`deepseek-v4-pro`/`minimax-m2.7`/`GLM-5.2` |
| 长期记忆（memory） | `gemini-3.8/3.7-flash`、基元律动 `deepseek-v4-pro`、商汤 `deepseek-v4-flash`、基元律动2 `minimax-m2.7`/`deepseek-v4-pro`/`qwen3.8` |
| 中期记忆（mid_memory） | `gemini-3.8/3.7-flash`、基元律动 `qwen3.8-max`、基元律动2 `qwen3.8` |
| 通用（utils） | `gemini-3.8/3.7-flash`、基元律动 `qwen3.8-max`/`deepseek-v4-pro`/`deepseek-v4-flash-0731`、基元律动2 `qwen3.8`/`deepseek-v4-pro` |
| 表达使用（expression_use） | `gemini-3.8/3.7-flash`、商汤 `deepseek-v4-flash`、基元律动2 `qwen3.8` |
| 表情包与视觉（emoji/vlm） | `gemini-3.8/3.7-flash`、`sensenova-6.8-flash-lite`、基元律动2 `qwen3.8` |
| embedding | `text-embedding-v4`（DashScope） |
| 学习（learner）、语音（voice） | 留空，分别回退到 utils 与原有选择逻辑 |

已知问题：`gemini` 供应商（`api.wanzhao-ysy.com` 中转）当前 API Key 无效，Core 日志持续出现 401 硬错误后回退成功，回复链路未中断但增加延迟与错误日志；这些硬错误还触发 MaiBot 看门狗自愈重启 bot.py，2026-09-13 活跃期观察到约每 10 分钟一次。配置中还登记了未被任务引用的 `qwen3.7-text-embedding`。模型登记或候选顺序不等于已逐一完成真实调用验收；目前仅文本回复经回退模型验证可用。embedding 自 `qwen-embedding` 变更为 `text-embedding-v4` 的时间与是否重建索引未记录，实际维度与存量索引一致性均未核验。

## 管理与网络

- Core 和 SnowLuma 管理端口均只绑定服务器回环地址，通过 SSH 隧道访问。SnowLuma noVNC 固定使用回环 `127.0.0.1:6081`，可供日常维护；OneBot `3001` 仅在 Compose 私有网络中提供给 Core Adapter。
- Caddy 管理代理当前未运行；若启动将公开 `8080`，使用 Basic Auth 反向代理至 Core；其 Basic Auth 与 WebUI Token 处于无 HTTPS 保护的链路中。
- `sqlite-web` 是未启动的可选只读管理服务，仍只绑定回环地址。
- Compose 使用私有 bridge 网络；SnowLuma OneBot WebSocket 使用 `3001`，不对主机公开。

## 明确限制与未核验项

- MCP 关闭，未配置 MCP 服务器。
- 未发现专用实时行情、交易、账户、下单、撤单或资金划转插件；但联网搜索、外部图片下载、EXIF 读取、坐标地理编码、群聊统计和第三方 Python 插件已启用。
- 不把模型输出、群消息或历史资料当作当前市场事实。
- Core 的 `plugin.permission` 含有 QQ 标识；其权限语义尚未按上游文档核验，因此 QQ 侧是否能触发特定插件动作不能作为已验证的安全保证。
- 未记录 Qwen/其他视觉模型的实际图片调用证据，也未记录 embedding 实际维度。
- 没有外部告警、自动恢复或本地升级备份；不得承诺恢复聊天记录、记忆、索引或 QQ 登录态。
- Core 健康检查仅探测 WebUI HTTP 接口，不覆盖插件运行时与适配器连通性；`healthy` 状态不代表消息链路可用（2026-09-14 故障证实）。IPC 插件运行时存在偶发 Runner 启动缺陷（上游问题），需 `--force-recreate` 恢复。
- 照片定位及每日分析的实际数据流与日志内容不符合“最小化处理、日志不记录不必要聊天数据”的原有期望；当前只记录该事实，未作配置修改。

## 变更约束

- 不修改 MaiBot 核心源码。
- 不通过日常启动或预检重写 `runtime/`；只有运营者明确授权时才可使用 `--reset-config --yes-reset-config`。
- 镜像升级必须固定 digest，并记录版本、Adapter commit、配置迁移与验证结果。
- 修改模型、人格、网络暴露、群范围或数据保留方式前，先核验当前配置和上游版本支持，再同步更新本文件、`README.md`、`AGENTS.md` 与审计文档。
