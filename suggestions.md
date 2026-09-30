# MaiBot OOM 排查结论与优化建议（2026-10-01）

本文是 2026-10-01 凌晨排查会话的总结。事实均有 journal/容器/源码证据；标注[推断]的为代码阅读估计，需 A/B 实测确认。

## 一、OOM 事实（journal 全量扫描，39 个 boot，回溯至 2026-08-13）

- **共 977 次 cgroup OOM 击杀**（8-14 起；journal 更早记录已轮转，真数 ≥ 977）。
- 签名完全一致：`Killed process (python)`、`CONSTRAINT_MEMCG`（容器限额级，非宿主机级）、bot.py 主进程 `anon-rss` 集中在 **860–905MB** 窄带（唯一离群值 9-29 22:09 的 1010MB）。
- 击杀间隔：活跃期最短 **7 分钟**（9-26 18:42→18:54→19:00→19:07→19:19 连击）；峰值段 8-30~9-9 平均 **25 次/天**。AGENTS.md 原记录"7 次/1.5–3 小时"严重低估。
- 零击杀时段：9-30 17:21 起 1536m+4GB swap 生效的 7.5 小时；以及低活跃 boot（如 9-27~9-28）。
- 2026-09-29 夜 7 次 + 9-30 开机后 1 次：与 AGENTS.md 记录精确吻合。

## 二、根因（已验证）

1. **上游 MaiBot 1.2.3 固有工作集 ≈ 容器 1050MB 峰值**（bot.py ~900MB + Runner ~120MB + 守护 ~30MB），启动基线即 ~625MB。`docker diff` 证明核心源码与镜像零差异（仅 charset_normalizer 被运行期 uv 重装），OOM 非本地改码引入。
2. **1024m 限额 < 工作集**，差距仅 ~30MB，任何波动（图片 VLM、embedding 回填）即击穿。
3. Python 堆不向 OS 归还内存（实测空闲 40 分钟 RSS 仅 634→625MB），棘轮式增长；看门狗自愈重启变相充当内存回收。
4. 宿主机 4GB 无 swap（撤回后）、Committed_AS ~10GB（2.6 倍超卖）：QQ ~630MB + 宝塔栈 ~450MB + MaiBot ~1GB 长期贴边，表现为 health check 超时抖动而非主机级击杀。
5. 10-01 凌晨 3 次宿主机重启（00:56/01:26/01:39）**非 OOM**（对应 boot 内核零击杀记录，且有 `Power key pressed short`），属运营者排障性重启。

## 三、当前生效状态（2026-10-01 03:00 核验）

- 按运营者要求已**撤回** 9-30 的 OOM 缓解：core `mem_limit: 1024m`、无日志轮转、宿主机无 swap；容器已按回退配置重建并核验。
- `talk_value` 已自 0.95 下调至 **0.75**（bot_config.toml 已改、core 已重启生效、AGENTS.md/PRD.md 已同步）。预期主动发言与完整 LLM 链路触发减少 ~21%，击杀间隔拉长，但不足以在 1024m 下根除 OOM。
- 消息链路正常：Core→snowluma:3001 TCP ESTABLISHED、Runner×3、healthy、登录 UIN 3582201576 唯一、3001 单监听。

## 四、优化建议（按性价比排序，均未实施）

### 方案一：计划性定时重启（不动任何配置，最贴合现状）
- 依据：bot.py 基线 625MB → 击杀线 ~880MB 需活跃期 2–6 小时。低风险时点（如 04:00/12:00/20:00）`docker restart maibot-core` 主动回收，RSS 常驻 650–750MB，把随机 OOM 变为基本不发生。
- 代价：重启瞬间丢进行中回复；有 Runner 环境变量缺陷（历史 8/490）与 Hook 注入失败的小概率，恢复手段成熟（`--force-recreate core` / `docker restart maibot-snowluma`）。

### 方案二：恢复 1536m + swap（数据支持的最小组合）
- 1536m+swap 生效的 7.5 小时零击杀 vs 峰值 25 次/天；1024m 与工作集差距仅 ~30MB。
- swap 缓解期间 0 使用——纯保险，不占内存（占 4GB 磁盘）。一条 compose 行 + 一个 swapfile 即可恢复。

### 方案三：宿主侧腾空间（宝塔栈 ~450MB → ~100MB，需运营者确认）
- 停 mysqld（零活动连接，且公网监听 3306）：-123MB
- nginx worker_processes 4→1：-110MB
- 停 php-fpm-82（无 PHP 站点）：-30MB
- 宿主 available 330MB → ~550MB，health check 抖动概率显著下降。

### 方案四：MaiBot 配置级瘦身（拒接 1–3 时才值得；合计预估 -180~350MB，均[推断]）
| 开关（bot_config.toml） | 预估 | 代价 |
| --- | --- | --- |
| 稀疏检索弃用 jieba 分词 | -60~80MB | 中文召回质量降 |
| `expression_selection_mode = "legacy"` | -30~60MB | 表达选择随机化 |
| 停 Pixiv/联网搜索/每日分析/EXIF 插件 | -40~80MB/个 | 功能消失 |
| `vector_pools mode = "dual" → 单池` | -30~80MB | 图谱检索弱化 |
| `enable_behavior_learning = false` | -20~50MB | 停止行为学习 |
- 注意：`max_reg_num`（表情包数量）与"思考时间"**不是**内存杠杆（表情只存元数据；等待不占内存）。
- 验证方法：每次只改一个开关 → `--force-recreate core` → 启动 10 分钟后对比 bot.py RSS 基线 625MB。

### 方案五：进一步降发言频率
- talk_value 已到 0.75；再降（0.6 以下）与"活跃气氛组"人格设定冲突，慎用。

### 根本解：扩内存至 8GB
- 所有配置手段都在 4GB 前提下打转；升配后 1536m 限额可永久保留，问题整体消失。

## 五、伴随发现的外部问题（与 OOM 无关，待处理）

1. **基元律动余额耗尽**：`deepseek-v4-pro`/`v4-flash-0731` 持续 402 `INSUFFICIENT_BALANCE`（10-01 01:33）——回退链在付费通道上是断的，需充值或调整候选。
2. **gemini 中转状态变化**：不再是 AGENTS.md 记录的 401；现为 503"并发上限"+响应被 max_tokens 截断（过载但 Key 可用）。
3. **记忆内核向量通道降级**：`embedding_fingerprint_unavailable`，双池退化单池运行（与上述供应商问题相关）。
4. journal 占磁盘 1.9GB、app 日志 329MB、prompt_imgs 3.3GB（2418 张）——磁盘卫生项，可设 `SystemMaxUse=200M` 与定期清理。

## 六、监控命令

```bash
# OOM 击杀计数（>0 即发生）
docker exec maibot-core cat /sys/fs/cgroup/memory.events
# bot.py RSS（替换为实际 bot.py PID）
docker exec maibot-core sh -c 'grep VmRSS /proc/9/status'
# 历史击杀记录
journalctl -k --no-pager | grep "Memory cgroup out of memory"
```
