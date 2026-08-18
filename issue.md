# A_Memorix 片段分段持续降级（llm_generate_failed）

> 严重程度：中（功能降级，不崩溃）。复发性问题（08-11 / 08-13 / 08-14 均出现）。
> 与 P0 插件运行时宕机**相互独立**：分段是内核功能，插件运行时停摆后仍会触发。

## 现象

`A_Memorix.EpisodeService` 周期性连续降级，每次约 6 条、间隔约 35s：

```
08-14 01:21:01 [WARN] A_Memorix.EpisodeService Episode segmentation fallback: source=chat_summary:f2928cc022e8eb182e9d8aa7064b4006 size=20 err=llm_generate_failed
08-14 01:21:42 [WARN] A_Memorix.EpisodeService Episode segmentation fallback: source=chat_summary:f2928cc022e8eb182e9d8aa7064b4006 size=20 err=llm_generate_failed
08-14 01:22:18 [WARN] A_Memorix.EpisodeService Episode segmentation fallback: source=chat_summary:f2928cc022e8eb182e9d8aa7064b4006 size=20 err=llm_generate_failed
08-14 01:22:52 [WARN] A_Memorix.EpisodeService Episode segmentation fallback: source=chat_summary:f2928cc022e8eb182e9d8aa7064b4006 size=20 err=llm_generate_failed
08-14 01:23:27 [WARN] A_Memorix.EpisodeService Episode segmentation fallback: source=chat_summary:f2928cc022e8eb182e9d8aa7064b4006 size=20 err=llm_generate_failed
08-14 01:24:00 [WARN] A_Memorix.EpisodeService Episode segmentation fallback: source=chat_summary:f2928cc022e8eb182e9d8aa7064b4006 size=20 err=llm_generate_failed
```

系统已优雅降级（fallback 按尺寸默认切分），不崩溃，但 A_Memorix 片段质量下降。

## 根因（代码级定位）

### 失败点：错误细节被丢弃

`llm_generate_failed` 抛出于 `src/A_memorix/core/utils/episode_segmentation_service.py:344-347`：

```python
result = await generate_with_resolved_model(resolved_model, ...)   # line 337
success = bool(result.success)
response = str(result.completion.response or "")
if not success or not response:
    raise RuntimeError("llm_generate_failed")   # ← line 347：丢弃一切细节
```

`result` 里的 `model_name`、HTTP 错误码、错误消息、token 数全部被丢弃，只剩一个归类字符串。

### 吞错误的位置

`episode_service.py:492-493` catch 后记成 `err=llm_generate_failed`：

```python
except Exception as e:
    logger.warning(f"Episode segmentation fallback: source=... err={e}")  # e 就是上面那个字符串
```

### 任务路由

`episode.segmentation_model` 当前为默认值 `"auto"`（无显式配置，`episode_segmentation_service.py:90`）。`auto` 模式下 `pick_text_generation_task`（`model_routing.py:74-84`）按 `("memory", "utils", "replyer", "planner", "tool_use")` 优先级选中 **memory 任务**的模型列表轮询：

```toml
# model_config.toml
[model_task_config.memory]
model_list = [
    "deepseek-v4-flash",
    "GLM5",
    "基元律动deepseek-v4-pro",
    "商汤deepseek-v4-flash",
]
```

### 为什么无 model_utils 日志、无 llm_error 文件

只有 `success=False`（HTTP 错误）才会触发 `model_utils` 的 WARN 和 `llm_error/` 落盘（对比 emoji 任务的 400 每次都被记录）。

01:21–01:24 失败窗口内，**除了 6 条 EpisodeService 警告，零条 model_utils 记录，也没有生成任何 llm_error 文件**。

这说明最可能是 **`success=True` 但 `response=""`**——模型调用"成功"了，却返回空内容。这完全解释了静默失败：不触发任何错误日志分支。

### 与历史失败的区别

08-11 那批 `final_failed` 是当时配置里的 `LLMX/gpt-5.6-terra` 触发 120s 硬超时 + 503，有完整 model_utils 记录（该 provider 已从当前配置移除）。当前这批（08-14）是**静默失败，无 HTTP 错误**，属另一类失败。

## 影响

- 已优雅降级（fallback 按尺寸默认切分），不崩溃。
- A_Memorix 片段质量下降。
- 复发性问题（08-11 / 08-13 / 08-14 均出现）。
- 不受 P0（插件运行时宕机）影响：EpisodeService 在插件运行时停摆后仍正常记录。

## 修复方案

问题在于错误信息被代码吞了，当前不知道是哪个模型、为什么返回空，因此盲改配置是赌博。分两步进行。

### 第一步：诊断（拿真实失败原因）

容器内临时 patch `episode_segmentation_service.py:344-347`，把 `result` 详情记到日志（哪个模型、success、response 前若干字符），restart core，等下次分段触发（约每小时一次），读日志拿根因：

```python
# 临时诊断 patch（替换 line 344-347）
success = bool(result.success)
response = str(result.completion.response or "")
if not success or not response:
    logger.warning(
        f"[diag] segmentation failed: model={result.completion.model_name} "
        f"success={success} response_len={len(response)} "
        f"response_preview={response[:200]!r}"
    )
    raise RuntimeError("llm_generate_failed")
```

约束：`/MaiMBot/src/A_memorix` 是镜像内上游代码，非 bind mount（compose 只挂了 `plugins`）。容器内改动 `docker-compose restart` 可保留，但 `down/up` 或重建会丢失。这是临时诊断手段，不是持久修复。

### 第二步：对症修复（拿到根因后）

取决于第一步的发现：

| 诊断结果 | 修复 |
|---|---|
| 某模型返回空 response | 从 memory 任务移除该模型，或显式配 `episode.segmentation_model` 指向稳定单模型 |
| 某模型触发 HTTP 错误（之前被吞） | 移除/替换该模型 |
| prompt 过长导致截断返回空 | 调整分段窗口大小 |
| 全模型间歇性返回空 | 上游 line 344-347 吞错误是设计缺陷，需上游修复或容器内持久 patch |

### 持久修复的现实

本仓库是部署配置仓库，不含上游源码。能持久落地的只有**配置层**（`model_config.toml` 的 memory 任务、或 A_Memorix 的 `episode.segmentation_model`）。上游代码缺陷（吞错误）需要上游 PR 或容器内 patch（不随镜像更新持久）。

## 相关文件

| 路径（容器内） | 作用 |
|---|---|
| `src/A_memorix/core/utils/episode_segmentation_service.py:344-347` | 失败点：丢弃 result 详情 |
| `src/A_memorix/core/utils/episode_service.py:492-493` | catch 点：记成 llm_generate_failed |
| `src/A_memorix/core/utils/model_routing.py:137-185` | `generate_with_resolved_model` 包装器 |
| `src/common/data_models/llm_service_data_models.py:84` | `LLMServiceResult` 结构（success/completion/response） |
| `runtime/core-config/model_config.toml:265` | `[model_task_config.memory]` 任务模型列表 |
