# 部署未决项与人工操作

本文件只记录需要运营者提供或在外部控制台完成的事项；不得填入密钥、群号、二维码或聊天记录。

## 阻塞实际接入的输入

- [ ] 已阅读并接受锁定 MaiBot 1.0.12 镜像的 EULA 与隐私条款，并将 `.env.example` 注释给出的精确 EULA/隐私确认值写入忽略的 `.env`；镜像升级时必须重新确认。
- [ ] 机器人 QQ 号、唯一生产群号和管理员 QQ 号已填入 `.env`。
- [ ] 已生成独立随机的 `WEBUI_ACCESS_TOKEN`（至少 20 字符），并填入 `.env`；不能与模型 key、NapCat token 或 QQ 密码复用。
- [ ] 已生成独立随机的 `NAPCAT_WEBUI_TOKEN`（至少 20 字符），并填入 `.env`；不能与 core WebUI token、NapCat WS token、模型 key 或 QQ 密码复用。
- [ ] DeepSeek key 与当前可用的文本模型 ID 已填入 `.env`；M0 不能在没有有效 key 的情况下完成真实消息往返。
- [ ] 已在 NapCat 的本机 WebUI 完成扫码登录，并核对 bootstrap 预置的正向 WebSocket `3001` 仍启用、token 与 `.env` 的 `NAPCAT_WS_TOKEN` 一致。
- [ ] 已确认生产群允许该 QQ 小号入群并收发消息；群白名单不会自动加入或邀请机器人。

## M2 前仍需确认

- [ ] DashScope key 与实际 Qwen-VL 模型 ID。
- [ ] 火山引擎 key、豆包视觉模型 ID，以及 `doubao-embedding-vision` 的实际 embedding 维度。当前 `1024` 仅来自上游默认值，不能据此替代供应商确认。
- [ ] 经人工审核、许可可用的 `common` 与 `crypto` 静态资料；不得把群消息或模型生成结论直接导入知识库。

## 已核验的实现事实（2026-07-28）

- MaiBot 源码 tag `1.0.12` 指向 `18f86829de6452b69f4eba14c38531678a585087`，Dockerfile 使用 Python 3.13；源码本地校验最低要求为 Python 3.12。
- 固定镜像（amd64）：`sengokucola/maibot@sha256:cceee3284a03eef34105a1855155e882ab36325fda03dd101000c6f4b26e165e`（tag `1.0.12`）、`mlikiowa/napcat-docker@sha256:11d72e50b6edc01b20f1a7611a250720e61412fe96184e3c70c3b8cf976744e1`（tag `v4.18.13`）和 `coleifer/sqlite-web@sha256:1e5b86237968ed747554f951c6df2fc2fe4bf4ef070b8ca23d553d7f6c6426f7`。
- MaiBot `1.0.12` 的配置版本为 `bot_config=8.14.28`、`model_config=1.17.6`；NapCat Adapter 当前核验提交为 `e34e286fa9c6f70e5c6aa3dc828451ab52c26773`，插件配置版本为 `0.1.0`。
- 适配器使用正向 WebSocket，默认端口 `3001`，并原生支持群/私聊 whitelist；本部署仅设置一个群 whitelist 且私聊列表为空。
- 上游仓库目前也可见 tag `1.1.0`。本项目仍按已确认范围锁定 `1.0.12`，不会自动升级；后续升级必须重新审计镜像 digest、配置迁移和适配器兼容性。
