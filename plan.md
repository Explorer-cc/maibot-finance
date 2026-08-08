# NapCat 切换至 SnowLuma 实施计划

## 目标

将生产 QQ 接入从 NapCat 和 `MaiBot-Napcat-Adapter` 切换到 SnowLuma 和 `MaiBot-SnowLuma-Adapter`，同时保持 MaiBot Core 的数据面不变：

- 保留同一个 `runtime/data/MaiMBot`，包括 `MaiBot.db`、A_Memorix、聊天记录、人物画像、群摘要、行为/表达学习、插件数据和 `emoji/`。
- 保留同一个 Core 配置、模型配置、唯一群白名单、空私聊白名单及现有插件启用状态，除 QQ Adapter 必要配置外不改变人格或聊天策略。
- SnowLuma 使用与当前机器人相同的 QQ 账号、相同的生产群，并在 MaiBot 中保持 `platform = "qq"`、`account_id = <机器人 QQ>`、`scope = "primary"`，使其解析到既有聊天流。
- 生产时只允许一个 QQ Adapter 接管该账号并向 Core 路由消息；切换后 SnowLuma 替代 NapCat 的 QQ 网关角色。

这不是承诺零中断或零协议差异：切换窗口会短暂中断 QQ 收发，且消息 ID、NapCat 私有动作和特殊消息段的兼容性必须验证后才能宣布完成。

## 当前实施状态（2026-08-09）

- 已完成维护窗口直切换：SnowLuma 已作为唯一生产 QQ 网关运行；NapCat 容器和 NapCat Adapter 均保持停止/禁用，未删除其数据或配置。
- 已验证 Core 为 `healthy`，并通过 Compose 私有网络连接 `snowluma:3001`；唯一群的入站文本与机器人出站回复已经实际验证。
- Core 继续使用原 `runtime/data/MaiMBot`，未迁移或重置数据库、记忆、聊天记录、表情或 Core 配置。旧表情/GIF、语音、文件与特殊消息段仍属未核验项。
- 首次登录临时 noVNC 宿主机映射已撤销；SnowLuma 仅保留回环 WebUI `127.0.0.1:5099`，OneBot `3001` 不对宿主机公开。
- 运营者已再次接受明文 HTTP 风险，`public-maibot-admin` 已恢复并公开 `8080`；SnowLuma 与 NapCat 均未暴露至公网。
- 维护窗口前创建的完整私有回滚备份仍保留；须完成稳定观察并由运营者确认精确目标后才可删除。

### 当前本机 SSH 转发基线

运营者的本机 SSH 配置应保留 `20003 → 127.0.0.1:18001` 访问 MaiBot WebUI，并新增 `20004 → 127.0.0.1:5099` 访问 SnowLuma WebUI。旧的 `20002 → 127.0.0.1:6099` 可移除，因为 NapCat 已停止；不得配置 `20005 → 6081`，因为首次登录用 noVNC 宿主机映射已经撤销。修改 SSH 配置后重新建立 SSH 连接才会生效。

## 已确认的实施决策

- 运营者接受维护窗口停机直切换：在 SnowLuma 部署、Adapter 安装与生产 QQ 登录前，先停止 `maibot-core`、`maibot-napcat` 和 `public-maibot-admin`。不采用在线并行运行或测试账号方案。
- 初始切换直接使用现有生产机器人 QQ 账号；SnowLuma 不会与 NapCat 同时登录该账号，登录和最小验证均在维护窗口进行。
- 运营者接受 SnowLuma Docker 框架所需的 `SYS_PTRACE` 与 `seccomp=unconfined` 权限，并接受 SnowLuma EULA、隐私条款及非官方 QQ 接入风险。
- 首次 SnowLuma QQ 登录使用 noVNC。noVNC 仅在维护窗口通过 SSH 临时转发访问；登录完成后撤销 noVNC 的宿主机端口映射和本地 SSH 转发。

## 端口、SSH 与秘密方案

当前受控管理入口保持不变：MaiBot WebUI 为服务器 `127.0.0.1:18001`，本机 SSH 转发 `20003 → 18001`；NapCat WebUI 为服务器 `127.0.0.1:6099`，本机 SSH 转发 `20002 → 6099`。公网 `8080` 仅为现有 Caddy 到 MaiBot WebUI 的明文 HTTP 代理，不扩展到 SnowLuma。

新增 SnowLuma 的管理入口如下：

| 入口 | 服务器绑定 | 本机 SSH 转发 | 保留时间 |
| --- | --- | --- | --- |
| SnowLuma WebUI | `127.0.0.1:5099` | `20004 → 5099` | 日常受控管理 |
| SnowLuma noVNC | `127.0.0.1:6081` | `20005 → 6081` | 仅首次生产 QQ 登录维护窗口 |
| SnowLuma VNC | 不映射 | 不转发 | 永不开放 |
| OneBot WebSocket | Compose 私有网络 `snowluma:3001` | 不转发 | 仅 Core Adapter 使用 |
| OneBot HTTP | 不映射 | 不转发 | 本方案不使用 |

无需修改服务器 SSH 配置或防火墙。SSH 转发是运营者本机配置：可在本机 `~/.ssh/config` 临时加入上述两条 `LocalForward`，也可只在连接命令中临时使用 `-L`。noVNC 登录完成后删除/停用 `20005 → 6081`；不删除日常 WebUI 的 `20004 → 5099`。

私有 `.env` 新增且必须互不复用的值：

```env
SNOWLUMA_IMAGE=<经审查且固定的镜像 digest>
SNOWLUMA_WS_TOKEN=<新的随机 OneBot Token，至少 20 个字符>
SNOWLUMA_WEBUI_PORT=5099
SNOWLUMA_VNC_PASSWORD=<新的独立随机密码>
SNOWLUMA_ACCEPT_EULA=1
SNOWLUMA_ACCEPT_PRIVACY=1
```

SnowLuma WebUI 管理员密码由 SnowLuma 首次初始化并写入其独立持久化配置；不得与上述 Token 或任何现有 MaiBot/NapCat Token 复用。所有值仅存在私有 `.env`/`runtime/`，不得写入本文档、Git、日志或聊天记录。

## 不可变的数据与安全边界

以下目录和配置为现有生产事实源，实施中不得重建、覆盖、导出或提交：

- `runtime/data/MaiMBot/`：Core 数据库、聊天记录、长期/中期记忆、表情文件、插件数据与日志。
- `runtime/core-config/`：现有 `bot_config.toml` 和 `model_config.toml`。
- 私有 `.env`、QQ 登录态、Token、媒体、数据库与日志。

禁止使用 `deploy/bootstrap.py --reset-config --yes-reset-config`。切换不改变群白名单、私聊边界、MCP 状态或已有第三方插件的数据流。SnowLuma 的 WebUI、VNC/noVNC、OneBot HTTP/WS 不得加入公网代理；生产管理入口继续使用受控 SSH 转发。

## 前置决策与准入

1. **授权与版本锁定**：确认 SnowLuma EULA 对其 native addon、Docker 镜像或自动化部署的许可。选择经审查的 SnowLuma Release、Docker 镜像 digest 及 `MaiBot-SnowLuma-Adapter` commit；不得使用 `latest` 或浮动分支。
2. **宿主机能力**：核验 CPU 架构、磁盘、内存和 Docker 安全策略。官方 Docker 框架要求 `SYS_PTRACE` 与 `seccomp=unconfined`；这构成比当前 NapCat 更高的容器权限，必须单独接受。
3. **兼容性清单**：列出现有插件所调用的 `adapter.napcat.*` 接口。SnowLuma Adapter 虽兼容多项同名接口，但每一项实际行为必须以固定版本的代码与受控验证为准。
4. **回滚资料**：在维护窗口前离线、受保护地备份 `runtime/data/MaiMBot` 和现有 NapCat 配置/Adapter commit；不得把备份提交到仓库或外发。当前没有既有升级备份，因此这一步是切换前置条件。

## 阶段一：停机前预置 SnowLuma

1. 在 `compose.yaml` 增加独立 `snowluma` 服务和仅首次登录使用的 noVNC Compose 覆盖文件；此时不启动 SnowLuma。
2. SnowLuma 使用独立的运行数据目录和 QQ 客户端登录目录；严禁与 `runtime/data/qq` 共享登录态。
3. SnowLuma 配置独立的 WebUI 密码、OneBot access token 和持久化目录；所有新秘密只放私有 `.env` 或 `runtime/`。
4. SnowLuma WebUI 绑定服务器回环地址，例如 `127.0.0.1:<新端口>:5099`。首次生产 QQ 登录期间临时将 noVNC `6081` 绑定到 `127.0.0.1`；完成登录后移除该宿主机映射，VNC `5900` 始终不映射到宿主机。
5. OneBot WebSocket `3001` 只在 Compose `maibot` 私有网络监听，不映射到主机。SnowLuma Adapter 将连接服务名 `snowluma:3001`。
6. 因运营者选择直接迁移生产账号，本阶段只完成镜像、容器、网络、持久化目录、私有环境变量和禁用 Adapter 的准备，不启动 SnowLuma 的生产 QQ 登录，也不创建额外 QQ 会话。
7. 完成本阶段后，确认 `snowluma` profile 尚未启动，Core 仍未加载 SnowLuma Adapter；随后进入维护窗口，不再进行在线并行验证。

## 阶段二：维护窗口停机与 Adapter 准备

执行本阶段前，运营者明确确认开始维护窗口。先停止 Core、NapCat 与公网管理代理；维护期间不接受 QQ 消息收发或 WebUI 管理。

1. 停止 `maibot-core`，冻结新的聊天记录、记忆和表情写入。
2. 停止 `maibot-napcat`，确认生产 QQ 不再由 NapCat 登录。
3. 停止 `public-maibot-admin`，使公网管理入口在维护期间不再代理 Core。
4. 将固定 commit 的 `MaiBot-SnowLuma-Adapter` 安装到现有 Core 插件目录，初始保持 `enabled = false`。
5. 通过 Core 既有插件安装/依赖机制安装声明依赖（包括 `silk-python`）；不得无审查地运行来源不明的插件代码。
6. 配置 SnowLuma Adapter：

   ```toml
   [plugin]
   enabled = false
   enable_private_chat_tool = false

   [luma_client]
   server = "snowluma"
   port = 3001
   token = "独立且不复用的 SnowLuma OneBot Token"
   connection_id = "primary"

   [chat]
   enable_chat_list_filter = true
   group_list_type = "whitelist"
   group_list = ["当前唯一生产群号"]
   private_list_type = "whitelist"
   private_list = []

   [filters]
   ignore_self_message = true
   ```

7. 保持 NapCat Adapter 的现有配置文件不变但禁用其运行；两套 Adapter 绝不同时对同一生产 QQ 账号启用。
8. 核验 SnowLuma Adapter 配置将上报相同的 `platform = "qq"`、相同机器人 `account_id` 和相同 `scope = "primary"`。这保证 Core 启动后延续既有 `chat_sessions`，而不是创建新的群会话。

## 阶段三：停机状态下的离线与静态验证

在不登录生产 QQ、不改变生产群白名单和不使用生产私聊的前提下完成。

1. **数据连续性**：在副本或只读查询中记录生产群的 `chat_sessions` 行（`platform`、`account_id`、`scope`、`group_id`）以及数据库和 `emoji/` 的完整性；确认 SnowLuma Adapter 的路由元数据采用同一身份键。
2. **Adapter 配置与路由**：审查固定版本 Adapter 的 `platform = "qq"`、`protocol = "snowluma"`、`account_id`、`scope` 和 OneBot WS 认证实现；确认生产配置将采用 `connection_id = "primary"`。
3. **媒体与表情**：静态核验已有表情的 Base64 出站路径及 PNG、JPEG、GIF 的转换逻辑；确认 Adapter 生成 OneBot `image` 段（`base64://`、`file://`、`subType=1`）。实际 QQ 显示验证留在维护窗口的最小生产验证中。
4. **会话与记忆**：使用本地 fixture 或受控路由确认相同 QQ 群号/账号/scope 解析为既有会话；确认不重建索引、不改变 embedding 模型或维度。不得为了验证而修改生产记忆内容。
5. **插件回归**：验证当前启用的智能戳一戳、内部回复再审、Pixiv 图片、照片 EXIF 定位、每日群聊分析、联网搜索。重点检查它们对 `adapter.napcat.*` 的依赖；照片定位的 EXIF 与外部逆地理编码风险必须继续如实记录。
6. **失败判定**：若出现重复会话、重复回复、媒体发送失败、权限不足或 Adapter API 不兼容，则停止切换，保留 NapCat 生产链路，并记录差异后修复/复测。

## 阶段四：SnowLuma 登录、接管与恢复服务

1. 复核：Core 数据目录、Core 配置、模型配置、群白名单、私聊白名单、embedding 模型/维度和当前 `chat_sessions` 身份键均保持原样；NapCat 的容器定义、Adapter 文件和私有运行数据均保留，不删除。
2. 临时启用 SnowLuma noVNC 的服务器回环映射 `127.0.0.1:6081`，并在运营者本机建立 `20005 → 6081` SSH 转发；同时使用 `20004 → 5099` 访问 SnowLuma WebUI。
3. 启动 SnowLuma，在 noVNC 中启动 QQ、扫码登录原生产机器人账号并完成手机确认；在 WebUI 中确认实际 `account_id` 与原机器人 QQ 一致。
4. 在 SnowLuma WebUI 配置 OneBot v11 WebSocket 服务为内部 `3001`，写入新的 `SNOWLUMA_WS_TOKEN`，且不映射 `3001` 到宿主机。
5. 原子性地禁用 NapCat Adapter、启用 SnowLuma Adapter；SnowLuma Adapter 必须保留 `connection_id = "primary"`、原群白名单、空私聊白名单、自身消息过滤，且主动私聊工具保持关闭。
6. 启动 `maibot-core`，确认 Core 只拥有一个可用的生产 QQ 消息网关。
7. 在唯一生产群做最小验证：接收一条群文本、发送一条文本、发送一枚已有表情；不扩大测试范围，不触发主动私聊。
8. 检查 Core、SnowLuma 日志和 `chat_sessions`：不得出现新的错误群会话、重复事件或重复回复。
9. 在 QQ 登录态确认持久化后，移除 noVNC 的 `6081` 宿主机映射和本机 `20005 → 6081` 转发；`5900` 从始至终不开放。
10. 在最小验证通过后，按运营者决定恢复 `public-maibot-admin`；恢复前确认其现有明文 HTTP 风险仍被接受。

## 阶段五：稳定观察与收尾

1. 在约定观察期内持续检查 QQ 登录稳定性、OneBot 重连、消息重复、媒体/表情发送、记忆召回和已启用插件的错误日志。
2. 维持 NapCat 的数据与配置作为回滚材料，暂不删除容器定义或私有登录态。
3. 维护窗口生成的私有回滚备份仅保留到 SnowLuma 的生产验证和稳定观察通过；届时按运营者要求删除已确认不再需要的备份。删除前必须核对精确文件名和状态，不得使用宽泛递归删除。
4. 观察通过后，再由运营者明确决定是否删除 NapCat 服务及其私有运行数据；删除前确认目标和备份，不执行宽泛递归删除。
5. 在实际切换完成后，更新 `README.md`、`PRD.md`、`docs/implementation-audit.md` 与 `AGENTS.md`，如实记录 SnowLuma 版本/digest、Adapter commit、端口、权限、验证结果、许可与风险。

## 回滚方案

回滚触发条件：SnowLuma 无法稳定登录、OneBot 链路失败、媒体/表情不兼容、聊天流分叉、现有插件异常，或出现重复收发。

1. 禁用 SnowLuma Adapter 并停止 SnowLuma 对生产 QQ 的登录。
2. 恢复 NapCat 对同一机器人 QQ 的登录，启用原有 NapCat Adapter。
3. 保持 Core 的 `runtime/data/MaiMBot` 和 `runtime/core-config` 原封不动；不从 SnowLuma 数据回写或覆盖 MaiBot 数据库。
4. 验证 `platform = "qq"`、原 `account_id`、`scope = "primary"` 和原群会话恢复可用。
5. 保存无敏感信息的故障证据和版本信息，分析后再安排下一次受控切换。

## 完成标准

- Core 继续使用原 `MaiBot.db`、A_Memorix 和 `emoji/`，不做数据迁移或重建。
- 生产群持续使用同一个 `platform/account_id/scope/group_id` 会话身份；旧记忆和聊天上下文可继续被 Core 使用。
- SnowLuma 成为唯一启用的生产 QQ Adapter，NapCat 不再向同一 Core 路由生产事件。
- 单群白名单、私聊阻断、自身消息过滤及现有安全边界保持不变。
- 文本、@、图片、已有表情（含 GIF）、语音、文件、撤回/戳一戳等经实际验证的功能达到既定标准；未验证或不兼容项明确列出，不表述为已实现。
- NapCat 可在不触碰 Core 数据的情况下恢复，直至运营者明确确认迁移完成。
