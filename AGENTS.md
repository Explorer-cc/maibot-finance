# AGENTS.md

## 项目定位与当前事实

本仓库是 MaiBot 私有 QQ 群聊人格助手的部署配置与文档仓库，不是 MaiBot 上游源码。当前运行实例位于 Debian VM，由 Docker Compose 管理。

- `maibot-core`：MaiBot `1.2.3`，内置 WebUI `1.7.2`，当前为 `healthy`；Core schema `40`，已完成 `vector → vector_intent` 配置迁移核验。
- `maibot-snowluma`：SnowLuma `v1.14.3`，当前运行中；其容器具备 `SYS_PTRACE` 与 `seccomp=unconfined`。
- Adapter：MaiBot-SnowLuma-Adapter `403de73785d1755a9a6b9828e403ed30399b638d` 当前启用。NapCat Adapter 已禁用。
- `maibot-napcat`：NapCat `v4.18.18`，容器已从 Docker 移除（2026-09-14 核验 `docker ps -a` 无此容器）；`runtime/napcat-config/` 与 `runtime/backups/` 中的配置及回滚资料仍保留；不得与 SnowLuma 同时登录生产 QQ。
- `public-maibot-admin`：当前未运行；Compose 保留其配置，启动后会将公网 `8080` 以明文 HTTP 反向代理至 Core WebUI。
- Core WebUI 仅绑定服务器 `127.0.0.1:18001`，SnowLuma WebUI 仅绑定 `127.0.0.1:5099`，SnowLuma noVNC 固定绑定服务器 `127.0.0.1:6081`；本机 SSH 转发为 `20003 → 18001` 和 `20004 → 5099`。OneBot `3001` 不映射到宿主机。
- 已实际验证唯一白名单群的 SnowLuma 入站文本与 MaiBot 出站回复。旧表情/GIF、文件及其他特殊消息段尚未完成迁移后 QQ 验证，不得表述为已兼容；语音消息经 2026-09-12 日志证实会因 Core 容器无 ffmpeg 而降级为文本占位，正常语音输出未核验。
- 迁移前完整私有回滚备份仍在 `runtime/backups/`；稳定观察通过并由运营者确认精确目标前不得删除。NapCat 配置与私有登录态资料按运营者决定保留，不得自行删除。

运行配置的唯一事实源是私有 `.env`、`runtime/` 和实际容器。尤其是 `runtime/core-config/bot_config.toml` 与 `runtime/core-config/model_config.toml`；仓库文档、模板和生成器均不能覆盖它们。

## 已配置能力

- 单一 QQ 群白名单；私聊白名单为空；Adapter 过滤机器人自身消息。
- 人格、行为学习、表达学习、黑话学习、A_Memorix 查询、人物画像注入、人物事实写回和群摘要写回均已启用。
- 群聊 `talk_value = 0.75`（2026-10-01 自 `0.95` 下调），私聊 `talk_value = 0`，引用回复关闭，富回复关闭；`enable_talk_value_rules = false`（虽残留两条时段规则定义但未生效）。
- 图片处理模式为 `auto`；表情包收集开启，内容过滤关闭。
- MCP 关闭，且当前没有静态金融资料或金融资料索引。
- 已登记的 API 提供商为 `商汤deepseek`（token.sensenova.cn）、`DashScope`、`gemini`（api.wanzhao-ysy.com 中转，2026-10-09 实测整体 HTTP 403/Cloudflare 1010 不可用，模型定义与 Key 保留但已不挂任何任务）、`Agnes`（apihub.agnes-ai.com，免费档）、`InkStone`（discovery-api.intern-ai.org.cn）、`TierFlow`（tierflow.cn，2026-10-11 配额耗尽已不挂任务）和 `南梁API`（api.llm.pm，OpenAI 协议需 `/v1` 后缀，2026-10-11 登记并挂载 `deepseek-v4.1-flash`，直连实测 200，置于 replyer 与 utils 第二位，未分配其他任务）；`基元律动`、`基元律动2`、`tokneflux` 已不在当前配置中。各任务选择策略 `sequential`：InkStone `Agents-A1`（replyer 队首）/`deepseek-v4-flash-0731`（utils 队首）与南梁API `deepseek-v4.1-flash`（两者均第二位）居前，商汤 `sensenova-6.8-flash-lite`/`deepseek-v4-flash`/`glm-5.2` 居中（存在瞬态 tpm/rpm 429），`Agnes` 系列（免费档 429 频繁）居末——`mid_memory` 因无其他候选仍为 Agnes 居首；视觉任务以 `sensenova-6.8-flash-lite` 开头；embedding 使用 `text-embedding-v4`（实测维度 1024）。2026-10-09 逐一真实调用核验：`gemini-3.8/3.7-flash` 403 已从全部任务列表摘除；原错误 ID `商汤deepseek-v4-flash`/`商汤glm-5.2`（404）已更正为商汤端点真实 ID `deepseek-v4-flash`/`glm-5.2`（复核可用）。2026-10-11 再次逐一核验全部 16 个模型定义：`intern-s2`/`qwen3.8-27b` 返回 200 但 `choices` 为空的结构损坏响应（与生产 120s 硬超时一致）、`tierflow`/`tierflow_pro` 24h 内生产 403 `insufficient_user_quota` 826 次、`agnes-2.0-flash` 重试后仍 429，当日应运营者要求将此 5 个模型自全部任务列表摘除（定义与 Key 保留）并新增南梁API `deepseek-v4.1-flash`（replyer/utils 第二位），Core 已两次重启生效并复核 healthy/Runner/TCP 链路。修改前备份：`runtime/backups/model_config.toml.bak-20261011-214235`（历史 `...-20261009-112950`、`...-120013`）。未被任务引用的模型定义：`gemini-3.7/3.8-flash`、`qwen3.7-text-embedding`、`intern-s2`、`qwen3.8-27b`、`tierflow`、`tierflow_pro`、`agnes-2.0-flash`。embedding 指纹/维度仍未核验，记忆内核以 `embedding_fingerprint_unavailable` 降级单池运行。
- 第三方插件配置为启用的包括：智能戳一戳、内部回复再审、Pixiv 图片、照片 EXIF 定位、每日群聊分析和联网搜索。每日新闻、绘图、鹿管记录和 Emoji 文本选择插件配置为关闭。

## 文档优先级

1. 用户在当前任务中的明确指令。
2. 当前 `runtime/`、私有 `.env` 与实际容器状态。
3. `compose.yaml` 与运行脚本的可执行行为。
4. `PRD.md`、`README.md`、`docs/` 与部署说明。

文档与运行配置冲突时，更新文档，不得改写 `runtime/` 以迎合文档。不要把 Git 历史当作当前配置来源。

## 配置与版本规则

- 镜像、适配器、SnowLuma、NapCat、模型标识、端口和配置键必须以当前锁定版本的官方资料和运行配置为准；镜像使用 digest，不使用 `latest`。
- `runtime/` 是 Git 忽略的私有运行事实源。Core WebUI 的修改通过 bind mount 写入该目录；不得提交、导出或维护其 Git 基线副本。
- SnowLuma WebUI 修改会写入 `runtime/snowluma/`；MaiBot/插件后台修改会写入 `runtime/core-config/`、`runtime/data/MaiMBot/` 或数据库。它们不会自动同步回 Compose、模板、文档或 Git；是否即时生效取决于具体配置，必要时重启对应服务。
- 2026-10-11 实测：容器以 `bot.py` 为入口，该路径不启动 `src/main.py` 的配置 FileWatcher（全容器生命周期无「配置文件监视器已启动」日志），`runtime/core-config/` 下 `bot_config.toml`/`model_config.toml` 的直接文件修改不会热重载，必须重启 Core 才生效。
- `deploy/bootstrap.py --initialize` 只能创建缺失私有文件；`--reset-config --yes-reset-config` 会覆盖现有配置，只能在运营者明确要求恢复时使用。
- 当前 `scripts/start.sh` 与 `scripts/preflight.py` 仍保留旧阶段参数接口；它们不应被当作当前配置能力的证明，也不得用于重写现有 `runtime/`。
- `scripts/preflight.py` 只验证配置结构、端口约束、Token 和 Compose 渲染；它不验证模型实际调用、图片处理、聊天行为或 QQ 收发。
- embedding 模型或维度变更前必须核验供应商实际返回，并计划全量索引重建。

## 已知运行风险与恢复手段

- Core 健康检查仅探测 WebUI `8001` HTTP 接口，不覆盖 IPC 插件运行时与适配器连通性；`healthy` 不能作为消息链路可用性的证明。链路核验应依次确认：SnowLuma 日志出现 `login detected` 与 `[OneBot.WS-Server] [ws-default] listening 0.0.0.0:3001`、Core 到 `snowluma:3001` 的 TCP 连接、插件 Runner 进程存活。
- MaiBot `1.2.3` IPC 插件运行时存在偶发启动缺陷：Runner 进程以“缺少必要的环境变量: MAIBOT_IPC_ADDRESS, MAIBOT_SESSION_TOKEN”立即退出（退出码 1），宿主侧周期重试无法自愈，全部第三方插件不加载；`docker-compose --env-file .env -f compose.yaml up -d --force-recreate core` 可恢复。容器存续期内约 490 次进程启动中出现 8 次（2026-09-14 统计）。
- SnowLuma Hook 组件注入偶发失败（`[Hook] load failed ... COMPONENT_LOAD_FAILED`）会使 QQ 停留在 `login identity discovered; awaiting readiness`，`LoginProbe` 超时且 OneBot `3001` 不监听；`docker restart maibot-snowluma` 重试注入即可恢复，无需重新扫码（2026-09-14 验证）。
- MaiBot 进程内置看门狗会在 LLM 硬错误后自愈重启 bot.py，活跃期约每 10 分钟一次；容器 `RestartCount` 不反映该类重启。gemini Key 无效（401）是其已知诱因之一。
- 2026-09-14 00:48 双容器重启后上述两类故障同时发生，消息链路中断约 50 分钟（00:48–01:37），经 `docker restart maibot-snowluma` 与 `--force-recreate core` 恢复登录、OneBot 监听、适配器连接与插件加载；恢复后群内消息级收发尚未重新核验。
- 2026-09-28 22:00 双容器重启后上述两类故障再次同时发生（Runner 退出码 1 于 22:01:38、Hook 停留在 awaiting readiness 于 22:01:51），消息链路中断约 17 小时（22:01–次日 15:19），经 `docker restart maibot-snowluma` 与 `--force-recreate core` 恢复；恢复后登录、OneBot 监听、Core→snowluma:3001 TCP、Runner 进程与健康检查均已核验，群内消息级收发仍待真实群消息核验。
- 2026-09-30 核验：宿主机 4GB 内存（`Committed_AS` 约 10GB、available 常低于 400MB）。`maibot-core` 原 `mem_limit: 1024m` 长期不足：bot.py RSS 增长至约 900MB–1GB 即触发 cgroup OOM 击杀（journalctl 记录 2026-09-29 夜间 7 次，间隔 1.5–3 小时；2026-09-30 开机 6 分钟内复现 `memory.events` `oom_kill=1`、容器 `RestartCount 0→1`）。此前归因于 LLM 硬错误的部分 bot.py 重启实为 OOM 击杀。2026-09-30 曾将 core `mem_limit` 提至 `1536m`、为 core/snowluma 增加日志轮转并在宿主机增加 4GB swap（该时段 `memory.events` 无新增击杀）；2026-10-01 按运营者要求全部撤回（`mem_limit` 回 `1024m`、移除日志轮转与 swap），cgroup OOM 击杀风险恢复存在；扩内存至 8GB 仍为根本解。宝塔面板栈（nginx/php-fpm/mysqld 约 450MB，MySQL 无活动连接）按运营者要求保留。
- 2026-10-03 核验并调整：宿主机 4GB `/swapfile`（fstab 持久）当前处于激活，与上条“已移除 swap”的记录不符；按运营者要求将 `vm.swappiness` 由 `0` 改为 `100`（`/etc/sysctl.conf` 与 `/etc/sysctl.d/99-maibot-swap.conf` 已对齐，运行时已生效），受控压力测试验证可将约 600MB 冷页换出（node/mysqld/nginx/omp 为主，bot.py 约 32MB），`MemAvailable` 自 768Mi 回升至约 1.3Gi。swap 只缓解宿主机整机内存压力，不改变 cgroup 限额内的 OOM 行为。同日按运营者要求将 core `mem_limit` 由 `1024m` 提至 `1536m`：先 `docker update --memory 1536m --memory-swap 3072m` 在线生效（容器未重启、`RestartCount` 不变、healthy），`compose.yaml` 已同步；swap 额度随 Docker 默认 2× 规则升至 1536m，core 总额度（RAM+swap）3GiB。cgroup `memory.reclaim` 主动回收已实测有效（回收 200M 使 RSS 748→419MB、317MB 转 swap），定时回收方案已提出但未实施。
- 2026-10-03 17:37 宿主机重启（`uptime -s` 2026-10-03 17:37:14）后新故障模式：QQ 快捷登录态失效，QQ 停在扫码页且二维码过期，Hook 管道已连但 `login identity discovered` 不触发、OneBot `3001` 不监听、Core 适配器每 5 秒重连失败。此次 Runner 正常，非 IPC/Hook 注入缺陷；`docker restart maibot-snowluma` 无法恢复（其前提是登录态仍有效）。有效恢复路径（2026-10-03 实测）：容器内 `apt-get install xdotool` 后经 `DISPLAY=:1` 模拟点击刷新二维码——登录窗为 `QQ` 窗口 (800,300) 320x460，过期提示/刷新按钮在名为 `xmessage` 的窗口 (671,519) 578x96、按钮中心约 (960,585)；截图用容器内 ffmpeg `x11grab`。注意：视觉模型对屏幕坐标的估计不可靠，必须以 `xdotool getwindowgeometry` 为准；登录成功后不得再盲点该坐标（会误点主界面），点击前须校验 `xmessage` 窗口仍存在且几何未变。扫码后 Hook 自动确认登录、OneBot 监听、适配器自动重连，无需重启 core。2026-10-03 19:15 经 xdotool 刷新二维码、运营者经 noVNC 隧道（本地端口被拒时可用 `ssh -L 16081:127.0.0.1:6081` 换端口）扫码恢复：19:38:16 `login detected: UIN=3582201576`、19:38:24 OneBot `3001` 监听、Core→`snowluma:3001` ESTABLISHED、Runner 存活、Bridge 预热 8 群/6125 成员，链路核验至适配器连接层；群内消息级收发仍待真实群消息核验。
- 2026-10-03 20:10–20:51 消息链路二次中断（SnowLuma 侧全程健康，故障在 Core 侧）：20:10:32 适配器 WebSocket 以「未收到更多 WebSocket 消息，连接已结束」断开——snowluma WS 服务端在 Core 停止响应后关闭空闲连接；随后 Core 插件运行时进入关停（Runner shutdown reason=host_stop、优雅退出超时后 terminate）且不再自愈，Runner 与适配器均未拉起，出站全部 `未找到目标平台: qq`，静默失联约 36 分钟（群内 20:39 仍有入站消息仅因 snowluma 侧仍在接收）。经 `docker-compose --env-file .env -f compose.yaml up -d --force-recreate core` 恢复（仅重建 core，未动 snowluma，QQ 登录态保留）；重建后启动追赶期出现 SQLite `database is locked` 写入风暴、`route_message` 30 秒超时与 WS 二次掉线（20:48），为事件循环阻塞的瞬时现象，20:50:12 起恢复收发，20:51:20–59 群内文本与图片收发核验通过。两次 WS 掉线签名相同（Core 停止响应→服务端关空闲连接），结论：链路中断根因在 Core 插件运行时不自愈（MaiBot 1.2.3 已知缺陷家族）叠加启动追赶期 SQLite 单写者锁竞争放大事件循环阻塞，非 SnowLuma 缺陷；20:10 关停的最初触发（LLM 硬错误/看门狗）未在留存日志中定位。重建后 bot.py RSS 约 1.0–1.1GB（core `mem_limit 1536m` 的约 70%），内存压力仍是放大因素。
- 2026-10-09 00:37–11:05 消息链路第三次中断（SnowLuma 侧全程健康，QQ 登录与 OneBot 监听正常）：Core Host 事件循环于 00:37:44 起失速（Runner 健康检查超时，日志自述「排除 Host 事件循环失速」），supervisor 误判为 Runner 故障，先 terminate 掉仍在正常心跳的 Runner，再连续 3 次重启失败（`Runner RPC 连接已断开`/30s 连接超时），02:37 彻底放弃后链路死亡。铁证：被「判死」的 Runner 此后每 30 秒心跳直至重建容器（RPC debug 日志至 10:00 仍连续）。该时段 journalctl 无 OOM 击杀、无 `database is locked` 风暴；失速前最后业务活动为 00:23–00:28 WebUI 模型测试（`TierSense` Not Found、`deepseek-v4-flash-0731` 尝试失败），最初诱因未在留存日志中定位；当晚 Agnes 免费档 429 共 526 次但均自愈，非直接致死原因。经 `docker-compose --env-file .env -f compose.yaml up -d --force-recreate core` 恢复，恢复后 healthy、bot.py×2、Runner×2、Core→snowluma:3001 ESTABLISHED 均核验；群内消息级收发仍待真实群消息核验。

## 安全与数据边界

- 仅配置一个 QQ 群；陌生私聊与其他群不在 Adapter 白名单中。
- MCP 关闭，未发现专用行情、交易、账户或资金划转插件；但联网搜索插件启用内容抓取和多个搜索后端，照片定位插件会读取 EXIF 并调用外部逆地理编码服务，Pixiv 插件会下载外部图片。不得将系统描述为没有联网、文件处理或第三方工具能力。
- 每日群聊分析插件已启用自动汇总，空目标群列表按其实现表示所有活跃群；当前 Adapter 单群白名单限制了可见群，但插件自身没有重复设置该群白名单。智能戳一戳也配置为群聊和私聊均可响应，私聊实际仍由 Adapter 空白名单阻断。
- 照片定位插件会对群内图片和文件读取 GPS EXIF，在命中后向外部地理编码服务发送坐标并 @ 发图人回复地址；它还会将坐标与地址写入 Core 日志。该行为与最小化处理和日志脱敏要求冲突，必须在任何文档、排障或扩展决策中如实说明。
- 不得把模型回答、聊天记录或未导入资料表述为当前价格、公告或市场事实。
- Core 配置中存在非空 `plugin.permission` QQ 标识。其能够授予的实际插件动作尚未按上游文档核验，因此不得宣称“QQ 不能触发任何管理动作”。
- `public-maibot-admin` 当前未运行；其配置若启动将公开 HTTP `8080`，虽有 Caddy Basic Auth，但用户名、密码和 WebUI Token 在公网链路中不具备 HTTPS 保护。SnowLuma 与 NapCat 均没有公网代理。
- SnowLuma noVNC `6081` 日常固定映射到宿主机回环地址 `127.0.0.1`，供本机或 SSH 隧道维护；不得映射到公网地址。VNC `5900` 与 OneBot `3001` 均不映射宿主机。`compose.snowluma-login.yaml` 是历史兼容覆盖文件，不再用于改变 noVNC 端口暴露。
- 第三方插件与插件代码目录以读写方式挂载到 Core；启用插件可在 Core 容器内执行任意插件 Python 代码，且容器能读取运行配置和访问网络。插件安装、升级和启用必须单独审查来源、权限与数据流向。
- 运行期密钥、QQ 登录态、聊天记录、记忆、数据库、媒体和日志不得提交或外发。当前仅保留本次迁移前的私有回滚备份；不得将其表述为已验证的数据恢复保证。

## 文档要求

- 文档使用中文，只描述已配置、已验证的能力和明确限制；未验证能力标为“未核验”，不得写成已实现或既定目标。
- 任何人格、模型、端口、数据保留、网络暴露或 QQ 范围变更，都应同步更新 `PRD.md`、`README.md`、`docs/implementation-audit.md` 与本文件。
- 跨群或私聊隔离不在生产环境创建额外真实会话测试；应使用本地 fixture、受控路由或实现级测试。

## 常用检查

```bash
docker-compose --env-file .env -f compose.yaml ps
git diff --check
git status --short
rg -n "1\\.0\\.12|latest|实时行情|M[0-3]" README.md PRD.md AGENTS.md deploy docs knowledge .env.example
```
