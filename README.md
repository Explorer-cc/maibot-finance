# MaiBot 跨市场金融群聊人格助手

基于 [MaiBot](https://github.com/MaiM-with-u/MaiBot) 1.0.12 的 QQ 群聊拟人化智能体，定位为**跨市场金融群聊人格助手**。

麦麦（MaiSaka）是一个长期生活在 QQ 群里的数字人格——她是“越菜越爱玩”的激进投资损友：金融话题中会兴奋、反讽，并以夸张高风险策略推动讨论。

> 本仓库是部署配置与文档仓库，不是 MaiBot 上游源码。MaiBot 通过 Docker Compose 以锁定版本运行，不修改其核心源码。

## 当前状态

- **M0（已完成，2026-07-29）**：单群 allowlist 下的 `QQ → NapCat → MaiBot → DeepSeek → QQ` 最小闭环已通过真实消息往返验证。
- **当前后端配置基线（2026-07-29）**：已健康加载 DeepSeek `deepseek-v4-flash`、Qwen-VL（`qwen3-vl-plus`）与 Qwen embedding（`text-embedding-v4`），并在唯一群开启 MaiBot 原生行为/表达/黑话学习、表情包收集、A_Memorix 查询、人物画像注入和自动写回。`.env` 声明 embedding 维度为 `1024`，真实 API 响应仍待验证。
- **M2（配置基线已完成）**：当前模型、人格、A_Memorix 与关闭引用回复均已同步到配置生成器，并通过预检。
- **M3（规划，未实现）**：接入 `common`/`crypto` 静态金融知识库与受限财经新闻 MCP，并完成模型实际调用、来源可追溯检索、作用域隔离、故障降级与外部告警。

## 核心边界

以下边界是产品的硬约束，不是待办：

- 仅服务一个 allowlist 中的私有 QQ 群，拒绝其他群、陌生私聊与临时会话。
- **M2 不接入实时数据；M3 仅规划受限只读财经新闻 MCP，不接入行情、交易、下单、撤单或资金划转能力。**
- 金融话题遵循当前后端人格：可使用激进投资策略、梭哈和高杠杆等表达推动群聊讨论。
- 运行期密钥、QQ 登录态、真实聊天数据、数据库、向量索引与日志不入库。

## 技术架构

通过 Docker Compose 运行三个服务（见 [`compose.yaml`](compose.yaml)）：

| 服务 | 作用 |
| --- | --- |
| `core` | MaiBot 核心：人格表达、群聊观察、回复时机、关系记忆、插件与 WebUI |
| `napcat` | NapCat Adapter + NapCat：QQ 消息接入（社区 NTQQ 协议，需单独评估账号风险） |
| `sqlite-web` | 可选只读管理工具（`admin` profile），按需经 SSH 隧道启动 |

模型后端仅涉及 DeepSeek（chat）与 DashScope Qwen（VLM、embedding）。当前 A_Memorix 查询已启用；M3 再导入静态金融资料并验证其召回。

## 目录结构

```
.
├── compose.yaml        # 容器编排
├── .env.example        # 配置模板（真实 .env 不入库）
├── runtime/            # 运行期数据：配置、数据库、登录态、向量索引（不入库）
├── scripts/            # 启停、预检、知识 manifest 校验脚本
├── deploy/             # 部署引导脚本
├── knowledge/          # M3 静态金融资料与 manifest
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
