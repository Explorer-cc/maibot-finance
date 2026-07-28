# MaiBot 跨市场金融研究与风险教育助手

基于 [MaiBot](https://github.com/MaiM-with-u/MaiBot) 1.0.12 的 QQ 群聊拟人化智能体，定位为**跨市场金融研究与风险教育助手**。

麦麦（MaiSaka）是一个长期生活在 QQ 群里的数字人格——人格是「爱叭叭的毒舌损友」，金融是她擅长的领域而非全部存在方式。她能闲聊、吐槽、表达情绪，也能在讨论市场时进入更专注的研究状态；研究状态只提高术语密度，不切换成另一个角色。

> 本仓库是部署配置与文档仓库，不是 MaiBot 上游源码。MaiBot 通过 Docker Compose 以锁定版本运行，不修改其核心源码。

## 当前状态

- **M0（已完成，2026-07-29）**：单群 allowlist 下的 `QQ → NapCat → MaiBot → DeepSeek → QQ` 最小闭环已通过真实消息往返验证。
- **M1（待完成）**：验证 Qwen-VL、豆包视觉回退与豆包 embedding 的模型配置和非敏感图片解析；A_Memorix、金融检索和自动记忆写回保持关闭。
- **M2（待完成）**：导入通过 manifest 自动校验的 `common` 与 `crypto` 静态机制科普资料，验证可追溯检索与风险教育行为。

## 核心边界

以下边界是产品的硬约束，不是待办：

- 仅服务一个 allowlist 中的私有 QQ 群，拒绝其他群、陌生私聊与临时会话。
- **不接入实时行情、财报、公告数据，也不接入任何交易、下单、撤单、资金划转能力。**
- 金融回答保持风险教育定位：不保证收益、不带单、不荐股荐币、不返佣、不募资、不规避监管。
- 毒舌只影响语气，不得成为侮辱、骚扰、泄露隐私或绕过安全规则的理由。
- 运行期密钥、QQ 登录态、真实聊天数据、数据库、向量索引与日志不入库。

## 技术架构

通过 Docker Compose 运行三个服务（见 [`compose.yaml`](compose.yaml)）：

| 服务 | 作用 |
| --- | --- |
| `core` | MaiBot 核心：人格表达、群聊观察、回复时机、关系记忆、插件与 WebUI |
| `napcat` | NapCat Adapter + NapCat：QQ 消息接入（社区 NTQQ 协议，需单独评估账号风险） |
| `sqlite-web` | 可选只读管理工具（`admin` profile），按需经 SSH 隧道启动 |

模型后端通过配置切换，当前涉及 DeepSeek、Qwen-VL 与豆包。

## 目录结构

```
.
├── compose.yaml        # 容器编排
├── .env.example        # 配置模板（真实 .env 不入库）
├── runtime/            # 运行期数据：配置、数据库、登录态、向量索引（不入库）
├── scripts/            # 启停、预检、知识 manifest 校验脚本
├── deploy/             # 部署引导脚本
├── knowledge/          # M2 静态金融资料与 manifest
├── logs/               # 脱敏结构化日志
└── docs/               # 实现审计与待办事项
```

## 核心文档

文档发生冲突时按 [`AGENTS.md`](AGENTS.md) 中的优先级裁决；不要把历史决策记录当作当前配置来源。

- [`PRD.md`](PRD.md) — 产品需求基线与边界
- [`plan.md`](plan.md) — 执行顺序与验收项
- [`decision-log.md`](decision-log.md) — 关键决策记录
- [`personas.md`](personas.md) — L0 人格文本
- [`AGENTS.md`](AGENTS.md) — 仓库约定与配置/版本规则

## 许可证

[MIT](LICENSE)。
