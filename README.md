# MaiBot 跨市场金融群聊人格助手

基于 [MaiBot](https://github.com/MaiM-with-u/MaiBot) 1.1.4 的 QQ 群聊拟人化智能体。麦麦（MaiSaka）是一个长期生活在私有 QQ 群里的数字人格：平时正常闲聊；金融话题中保持“越菜越爱玩”的激进投资损友风格。

本仓库是部署配置与文档仓库，不是 MaiBot 上游源码。MaiBot 通过 Docker Compose 以锁定版本运行，不修改其核心源码。

## 当前运行基线

- MaiBot Core/WebUI：`1.1.4`；镜像以私有 `.env` 中的 digest 锁定。
- QQ 接入：NapCat Docker `v4.18.18` 与 MaiBot-Napcat-Adapter `85bec0059afed0a7fd83b35ff06d393114562f42`。
- 模型：当前配置登记 DeepSeek、DashScope、LLMX、ZhipuAI 四个 API 提供商；实际任务分配见 [`PRD.md`](PRD.md)。embedding 配置为 `qwen-embedding`、维度 `1024`，实际响应尚未记录。
- 群聊能力：唯一 allowlist 群、行为/表达/黑话学习、表情包收集、A_Memorix 查询、人物画像注入、群摘要与人物事实自动写回。引用回复和富回复均关闭。
- 插件：除 NapCat Adapter 外，当前配置还启用了智能戳一戳、内部回复再审、Pixiv 图片、照片 EXIF 定位、每日群聊分析和联网搜索插件；详细作用域与风险见 [`docs/implementation-audit.md`](docs/implementation-audit.md)。
- 已验证：Core 健康、NapCat 连接以及 QQ 消息收发正常。

## 运行边界

- 仅服务一个 allowlist 中的私有 QQ 群；拒绝其他群、陌生私聊和临时会话。
- MCP 保持关闭，当前未导入静态金融资料或建立金融资料索引。
- 未发现专用行情、交易、下单、撤单或资金划转插件；但联网搜索、图片下载、EXIF 定位、群聊统计和第三方 Python 插件均已存在，不能将本实例描述为“没有外部工具”。
- `core`、`napcat` 与 `sqlite-web` 仅绑定服务器 `127.0.0.1`。本机 SSH 配置保持 `20003 → 18001`（MaiBot WebUI）和 `20002 → 6099`（NapCat WebUI）。
- 当前 `public-maibot-admin` 公开 HTTP `8080` 并代理 Core WebUI；它使用 Basic Auth，但没有 HTTPS 保护。
- 运行期密钥、QQ 登录态、聊天记录、数据库、记忆、媒体和日志均在 Git 忽略的 `runtime/` 与 `.env` 中，不得提交。

## 技术架构

| 服务 | 作用 |
| --- | --- |
| `core` | MaiBot 核心：人格、群聊观察、回复、记忆、插件与 WebUI |
| `napcat` | NapCat 与 Adapter：QQ 消息接入；属于社区 NTQQ 协议方案，存在账号风险 |
| `sqlite-web` | 可选只读管理工具，按需通过 SSH 隧道使用 |
| `public-maibot-admin` | 当前运行的 Caddy 管理代理；公开 HTTP `8080` 并存在明文传输风险 |

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
