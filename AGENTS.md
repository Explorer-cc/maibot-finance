# AGENTS.md

## 项目定位与当前事实

本仓库是 MaiBot 私有 QQ 群聊人格助手的部署配置与文档仓库，不是 MaiBot 上游源码。当前运行实例位于 Debian VM，由 Docker Compose 管理。

- `maibot-core`：MaiBot `1.1.4`，当前为 `healthy`。
- `maibot-napcat`：NapCat `v4.18.18`，当前运行中。
- Adapter：`85bec0059afed0a7fd83b35ff06d393114562f42`。
- `public-maibot-admin`：当前运行中，并将公网 `8080` 以明文 HTTP 反向代理至 Core WebUI。
- Core WebUI 仍仅绑定服务器 `127.0.0.1:18001`，NapCat WebUI 仅绑定 `127.0.0.1:6099`；本机 SSH 转发为 `20003 → 18001` 和 `20002 → 6099`。

运行配置的唯一事实源是私有 `.env`、`runtime/` 和实际容器。尤其是 `runtime/core-config/bot_config.toml` 与 `runtime/core-config/model_config.toml`；仓库文档、模板和生成器均不能覆盖它们。

## 已配置能力

- 单一 QQ 群白名单；私聊白名单为空；Adapter 过滤机器人自身消息。
- 人格、行为学习、表达学习、黑话学习、A_Memorix 查询、人物画像注入、人物事实写回和群摘要写回均已启用。
- 群聊 `talk_value = 0.85`，私聊 `talk_value = 0`，引用回复关闭，富回复关闭。
- 图片处理模式为 `auto`；表情包收集开启，内容过滤关闭。
- MCP 关闭，且当前没有静态金融资料或金融资料索引。
- 已登记的 API 提供商为 DeepSeek、DashScope、LLMX 和 ZhipuAI。回复、规划和通用任务配置了 `GLM5`、`gpt-5.6-terra` 与 `deepseek-v4-flash` 候选模型；视觉任务配置了 `gpt-5.6-terra` 与 `qwen-vl`，embedding 使用 `qwen-embedding`。
- 第三方插件配置为启用的包括：智能戳一戳、内部回复再审、Pixiv 图片、照片 EXIF 定位、每日群聊分析和联网搜索。每日新闻、绘图、鹿管记录和 Emoji 文本选择插件配置为关闭。

## 文档优先级

1. 用户在当前任务中的明确指令。
2. 当前 `runtime/`、私有 `.env` 与实际容器状态。
3. `compose.yaml` 与运行脚本的可执行行为。
4. `PRD.md`、`README.md`、`docs/` 与部署说明。

文档与运行配置冲突时，更新文档，不得改写 `runtime/` 以迎合文档。不要把 Git 历史当作当前配置来源。

## 配置与版本规则

- 镜像、适配器、NapCat、模型标识、端口和配置键必须以当前锁定版本的官方资料和运行配置为准；镜像使用 digest，不使用 `latest`。
- `runtime/` 是 Git 忽略的私有运行事实源。Core WebUI 的修改通过 bind mount 写入该目录；不得提交、导出或维护其 Git 基线副本。
- `deploy/bootstrap.py --initialize` 只能创建缺失私有文件；`--reset-config --yes-reset-config` 会覆盖现有配置，只能在运营者明确要求恢复时使用。
- 当前 `scripts/start.sh` 与 `scripts/preflight.py` 仍保留旧阶段参数接口；它们不应被当作当前配置能力的证明，也不得用于重写现有 `runtime/`。
- `scripts/preflight.py` 只验证配置结构、端口约束、Token 和 Compose 渲染；它不验证模型实际调用、图片处理、聊天行为或 QQ 收发。
- embedding 模型或维度变更前必须核验供应商实际返回，并计划全量索引重建。

## 安全与数据边界

- 仅配置一个 QQ 群；陌生私聊与其他群不在 Adapter 白名单中。
- MCP 关闭，未发现专用行情、交易、账户或资金划转插件；但联网搜索插件启用内容抓取和多个搜索后端，照片定位插件会读取 EXIF 并调用外部逆地理编码服务，Pixiv 插件会下载外部图片。不得将系统描述为没有联网、文件处理或第三方工具能力。
- 每日群聊分析插件已启用自动汇总，空目标群列表按其实现表示所有活跃群；当前 Adapter 单群白名单限制了可见群，但插件自身没有重复设置该群白名单。智能戳一戳也配置为群聊和私聊均可响应，私聊实际仍由 Adapter 空白名单阻断。
- 照片定位插件会对群内图片和文件读取 GPS EXIF，在命中后向外部地理编码服务发送坐标并 @ 发图人回复地址；它还会将坐标与地址写入 Core 日志。该行为与最小化处理和日志脱敏要求冲突，必须在任何文档、排障或扩展决策中如实说明。
- 不得把模型回答、聊天记录或未导入资料表述为当前价格、公告或市场事实。
- Core 配置中存在非空 `plugin.permission` QQ 标识。其能够授予的实际插件动作尚未按上游文档核验，因此不得宣称“QQ 不能触发任何管理动作”。
- `public-maibot-admin` 当前公开 HTTP `8080`，有 Caddy Basic Auth，但用户名、密码和 WebUI Token 在公网链路中不具备 HTTPS 保护。NapCat 没有公网代理。
- 第三方插件与插件代码目录以读写方式挂载到 Core；启用插件可在 Core 容器内执行任意插件 Python 代码，且容器能读取运行配置和访问网络。插件安装、升级和启用必须单独审查来源、权限与数据流向。
- 运行期密钥、QQ 登录态、聊天记录、记忆、数据库、媒体和日志不得提交或外发。运营者未保留本地升级备份，不得承诺恢复这些数据。

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
