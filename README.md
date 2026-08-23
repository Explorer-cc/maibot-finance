# MaiBot 跨市场金融群聊人格助手

基于 [MaiBot](https://github.com/MaiM-with-u/MaiBot) 1.2.1 的 QQ 群聊拟人化智能体。麦麦（MaiSaka）是一个长期生活在私有 QQ 群里的数字人格：平时正常闲聊；金融话题中保持“越菜越爱玩”的激进投资损友风格。

本仓库是部署配置与文档仓库，不是 MaiBot 上游源码。MaiBot 通过 Docker Compose 以锁定版本运行，不修改其核心源码。

## 当前运行基线

- MaiBot Core/WebUI：`1.2.1`；镜像以私有 `.env` 中的 digest 锁定。升级已将 Core schema 从 `36` 迁移到 `40`，未重置数据库或 A_Memorix 数据。
- QQ 接入：SnowLuma `v1.14.3`（私有 `.env` 锁定 digest）与 MaiBot-SnowLuma-Adapter `403de73785d1755a9a6b9828e403ed30399b638d`。NapCat `v4.18.18` 及其 Adapter 已停止/禁用，作为回滚材料保留。
- 模型：当前配置登记 DeepSeek、DashScope、LLMX、ZhipuAI 四个 API 提供商；实际任务分配见 [`PRD.md`](PRD.md)。embedding 配置为 `qwen-embedding`、维度 `1024`，实际响应尚未记录。
- 群聊能力：唯一 allowlist 群、行为/表达/黑话学习、表情包收集、A_Memorix 查询、人物画像注入、群摘要与人物事实自动写回。引用回复和富回复均关闭。
- 插件：除 SnowLuma Adapter 外，当前配置还启用了智能戳一戳、内部回复再审、Pixiv 图片、照片 EXIF 定位、每日群聊分析和联网搜索插件；详细作用域与风险见 [`docs/implementation-audit.md`](docs/implementation-audit.md)。
- 已验证：Core 健康、SnowLuma 内网 OneBot 连接，以及唯一白名单群的文本收发。旧表情/GIF、语音、文件和特殊消息段尚未核验。

## 运行边界

- 仅服务一个 allowlist 中的私有 QQ 群；拒绝其他群、陌生私聊和临时会话。
- MCP 保持关闭，当前未导入静态金融资料或建立金融资料索引。
- 未发现专用行情、交易、下单、撤单或资金划转插件；但联网搜索、图片下载、EXIF 定位、群聊统计和第三方 Python 插件均已存在，不能将本实例描述为“没有外部工具”。
- `core`、`snowluma` 与 `sqlite-web` 的管理端口仅绑定服务器 `127.0.0.1`。本机 SSH 转发可使用 `20003 → 18001`（MaiBot WebUI）和 `20004 → 5099`（SnowLuma WebUI）；SnowLuma noVNC 固定绑定回环 `6081`，便于日常本机或 SSH 隧道维护；OneBot `3001` 不映射到宿主机。
- `public-maibot-admin` 当前未运行；其配置若启动会公开 HTTP `8080` 并代理 Core WebUI，虽使用 Basic Auth 但没有 HTTPS 保护。
- 运行期密钥、QQ 登录态、聊天记录、数据库、记忆、媒体和日志均在 Git 忽略的 `runtime/` 与 `.env` 中，不得提交。

## 技术架构

| 服务 | 作用 |
| --- | --- |
| `core` | MaiBot 核心：人格、群聊观察、回复、记忆、插件与 WebUI |
| `snowluma` | SnowLuma 与 SnowLuma Adapter：当前 QQ 消息接入；容器使用 `SYS_PTRACE` 与 `seccomp=unconfined`，存在非官方 QQ 接入风险 |
| `napcat` | 已停止的旧 QQ 接入与 Adapter；保留用于回滚，不与 SnowLuma 同时登录生产账号 |
| `sqlite-web` | 可选只读管理工具，按需通过 SSH 隧道使用 |
| `public-maibot-admin` | 当前未运行；配置保留，启动后公开 HTTP `8080`，存在明文传输风险 |

## 目录结构

```text
.
├── compose.yaml        # 容器编排
├── .env.example        # 配置模板；真实 .env 不入库
├── runtime/            # 配置、数据库、登录态、记忆与缓存；不入库
├── scripts/            # 启停、预检与资料 manifest 校验脚本
├── deploy/             # 私有运行配置初始化工具与部署说明
├── knowledge/          # 预留的静态资料目录；当前没有已导入资料
├── logs/               # 脱敏结构化日志
└── docs/               # 当前实现审计与运行事项
```

## 核心文档

- [`PRD.md`](PRD.md) — 当前产品范围、实际模型配置与能力边界
- [`deploy/README.md`](deploy/README.md) — 已有实例的受控运维
- [`AGENTS.md`](AGENTS.md) — 仓库约定

## 许可证

[MIT](LICENSE)。
