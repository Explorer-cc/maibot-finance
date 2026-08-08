# 静态资料目录

当前项目没有向 MaiBot 或 A_Memorix 导入任何静态金融资料，也没有建立金融资料索引。本目录仅保留为空目录与资料校验工具的使用位置；不得把群消息、聊天截图、模型输出、付费报告全文、实时行情或未经许可的网页抓取结果放入此处。

如未来经单独决策启用静态资料，每份文件应配套 JSON manifest，并先执行：

```bash
.venv/bin/python scripts/validate_knowledge_manifest.py knowledge/<file>.manifest.json
```

该校验只验证来源、许可证、资料域、日期和本地文件 SHA-256；通过校验不代表资料已经导入、被模型使用或适用于当前市场状态。
