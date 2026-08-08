# 本机 SSH 端口 `20004` 冲突记录

更新：2026-08-09

## 现象

运营者希望通过本机 SSH 转发访问 SnowLuma WebUI：

```text
127.0.0.1:20004 → 服务器 127.0.0.1:5099
```

执行 `ssh -N maibot` 时，本机 OpenSSH 报错：

```text
bind [127.0.0.1]:20004: Permission denied
Could not request local forwarding.
```

## 已确认事实

- 服务器端 SnowLuma WebUI 正常，仅绑定 `127.0.0.1:5099`；这不是服务器端端口、防火墙或 Docker 映射问题。
- Windows IPv4 TCP 排除端口范围不包含 `20004`，因此不是系统保留范围导致。
- 本机 `netstat` 显示 `127.0.0.1:20004` 已处于 `LISTENING` 状态，所有者为 `Code.exe`（VS Code）。
- 该 `Code.exe` 是 VS Code 内部 Node 服务；其启动参数未标识具体扩展或普通“端口 / Ports”面板可停止的转发。尝试在 Ports 面板停止转发后，监听仍存在。
- 当前没有修改服务器服务、SnowLuma、MaiBot、NapCat 或 `.env` 来规避该问题。

## 当前影响

- 日常 QQ、MaiBot、SnowLuma、Core WebUI 和公网 `8080` 管理代理均不受影响。
- 仅影响运营者本机以 `20004` 访问 SnowLuma WebUI；现有 SSH 配置因 `ExitOnForwardFailure yes` 会使包含该转发的 SSH 连接失败。

## 当前决定

- 不结束 `Code.exe` 或关闭 VS Code，因为运营者当前不能这样做。
- 不将 SnowLuma WebUI 改为公网暴露。
- 不将 noVNC `6081` 暴露到宿主机或写入 SSH 配置。
- 暂不把本机转发改为其他端口；这是运营者要求保留并解决 `20004` 冲突，而不是转移冲突。

## 后续恢复条件

当运营者能够关闭/定位占用 `20004` 的 VS Code 内部服务时，按以下顺序恢复：

1. 使用 `netstat -ano | findstr :20004` 确认没有监听结果。
2. 保持 SSH 配置中的 `LocalForward 127.0.0.1:20004 127.0.0.1:5099`。
3. 执行 `ssh -N maibot` 或 `ssh maibot`，确认 `ssh.exe` 成为 `127.0.0.1:20004` 的唯一监听者。
4. 在浏览器访问 `http://127.0.0.1:20004/`，确认可打开 SnowLuma WebUI。

未经运营者明确同意，不使用替代本机端口，也不终止 VS Code 进程。
