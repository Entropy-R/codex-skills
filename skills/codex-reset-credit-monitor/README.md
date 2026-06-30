# Codex Reset Credit Monitor

`codex-reset-credit-monitor` 是一个用于查看和监控 Codex reset credit 的 Codex skill。

它可以查询当前可用的重置机会数量、每次机会的到期时间、当前用量窗口，并把查询结果写入本地快照历史。它还可以生成和维护一个 Windows 计划任务，用较低成本定期记录 reset credit 状态，方便之后解释数量变化和临期风险。

## Usage

在 Codex 中直接调用：

```text
$codex-reset-credit-monitor
```

默认行为是查看当前可用 reset credit 数量和每个机会的到期时间。

状态输出会优先给出结论，然后用表格展示 reset credit 到期明细和当前用量窗口，最后给出是否需要使用 reset credit 的建议。

常见用法：

```text
使用 $codex-reset-credit-monitor 查看当前还有几次重置机会，以及分别什么时候到期
```

```text
使用 $codex-reset-credit-monitor 记录一次快照，并解释最近 30 天的变化
```

```text
使用 $codex-reset-credit-monitor 10h
```

只提供 `10h`、`1d`、`10hours`、`10小时` 这类时间表达式时，skill 会按对应周期安装或更新 Windows 计划任务。

```text
使用 $codex-reset-credit-monitor 查看计划任务是否正常
```

```text
使用 $codex-reset-credit-monitor 移除计划任务
```

## Script Commands

脚本命令主要用于排查、自动化和计划任务执行。日常使用优先通过 Codex 调用 skill。

```powershell
$script = "$env:CODEX_HOME\skills\codex-reset-credit-monitor\scripts\reset_credit_monitor.py"

python $script
python $script status
python $script snapshot
python $script history --days 30
python $script explain --days 30
python $script task generate --hours 6
python $script task install --hours 6
python $script task status
python $script task remove
```

如果没有设置 `CODEX_HOME`，通常可以使用 `~/.codex` 作为 Codex home。

## Data Boundary

这个 skill 会读取本机 Codex 登录态文件 `auth.json`，并向 ChatGPT backend 发起只读请求：

- `https://chatgpt.com/backend-api/wham/rate-limit-reset-credits`
- `https://chatgpt.com/backend-api/wham/usage`

它不会调用模型，不会兑换 reset credit，也不会输出 token、原始 `auth.json`、邮箱地址、user id 或 account id。

## Output Files

默认输出目录：

```text
$CODEX_HOME\status_snapshots\reset_credit_monitor
```

主要文件：

- `latest.json`：最近一次脱敏后的状态快照。
- `history.jsonl`：追加写入的历史快照。
- `monitor.log`：计划任务运行日志。
- `task\run_monitor.cmd`：Windows 计划任务执行的 wrapper。
- `task\install_task.ps1`：生成的安装辅助脚本。
- `task\remove_task.ps1`：生成的移除辅助脚本。
- `task\task_config.json`：生成的计划任务配置元数据。

## Notes

- 默认建议每 6 小时查询一次。
- 支持 `10h`、`1d`、`10hours`、`10小时`、`10 hr`、`2 days` 等时间表达式。
- 允许的计划任务间隔范围是 1 到 168 小时。
- Windows 计划任务只运行本地 wrapper 脚本，不唤醒 Codex 模型。
