# M2 静态金融知识资料

此目录只接收 `common` 与 `crypto` 静态机制科普资料。M1 只验证模型与图片解析，不在此目录新增资料，也不创建金融向量索引。不要放入群消息、聊天截图、模型输出、付费报告全文、实时行情或未经许可的网页抓取结果。

每份资料都需要一个相邻的 JSON manifest，并在导入前通过：

```bash
.venv/bin/python scripts/validate_knowledge_manifest.py knowledge/<file>.manifest.json
```

manifest 必须记录来源、机构、发布日期、导入日期、市场域、司法辖区、版本、可信度、许可证、适用期、状态和文件 SHA-256。校验通过表示元数据和本地文件完整；资料只有在许可证字段明确、域为 `common` 或 `crypto` 且校验通过后才可导入 A_Memorix。

M2 可由运营者经 SSH 隧道后的 MaiBot WebUI 导入已通过自动校验的资料，并保留导入记录与召回来源。资料准入不要求人工审核；不满足来源 HTTPS、许可证、允许域或 SHA-256 校验的资料不得进入 `runtime/` 或 A_Memorix 数据目录。
