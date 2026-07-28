# M2 静态知识资料

此目录只接收经人工审核、许可明确的 `common` 与 `crypto` 静态机制科普资料。不要放入群消息、聊天截图、模型输出、付费报告全文、实时行情或未经许可的网页抓取结果。

每份资料都需要一个相邻的 JSON manifest，并在导入前通过：

```bash
.venv/bin/python scripts/validate_knowledge_manifest.py knowledge/<file>.manifest.json
```

manifest 必须记录来源、机构、发布日期、导入日期、市场域、司法辖区、版本、可信度、许可证、适用期、状态、审核人和文件 SHA-256。校验通过只表示元数据完整，不代表资料已经获许可或已经导入 A_Memorix。

M2 的实际导入必须由管理员在 MaiBot WebUI 中逐批执行、保留导入记录并验证召回来源。没有通过来源/许可审查的资料不得进入 `runtime/` 或 A_Memorix 数据目录。
