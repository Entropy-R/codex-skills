---
name: codex-reset-credit-monitor
description: Monitor Codex usage-limit reset credits and manage a low-cost Windows Scheduled Task that periodically queries current reset-credit count, expiry times, local usage windows, snapshot history, and warning state. Use when the user asks to check Codex reset opportunities, see expiry times, explain reset-credit history, install or maintain a scheduled monitor, or troubleshoot the reset-credit monitoring task.
---

# Codex Reset Credit Monitor

Use this skill to manage a local reset-credit monitor for Codex.

## Quick Start

When the user invokes `$codex-reset-credit-monitor`, decide the operation from the request:

- If the user invokes only `$codex-reset-credit-monitor` with no extra instruction, run `status`.
- If the user invokes the skill with only a duration such as `10h`, `1d`, `10hours`, or `10小时`, install the scheduled task at that interval.
- Current count or expiry-time request: run `status`.
- Record the current state or update history: run `snapshot`.
- Explain recent changes: run `history` or `explain`.
- Generate wrapper scripts or customize polling interval: run `task generate --hours N`.
- Install, inspect, run, or remove the scheduled task: run the matching `task` command. `task install --hours N` regenerates wrapper scripts before registering the task.

Bundled script commands:

```powershell
$script = "$env:CODEX_HOME\skills\codex-reset-credit-monitor\scripts\reset_credit_monitor.py"
python $script
python $script 10h
python $script status
python $script snapshot
python $script history --days 30
python $script explain --days 30
python $script task generate --hours 6
python $script task generate --every 1d
python $script task install --hours 6
python $script task install --every 10小时
python $script task status
python $script task remove
```

If `CODEX_HOME` is not set, use your Codex home directory, usually `~/.codex`.

## Responsibilities

- Query current Codex reset credits from `https://chatgpt.com/backend-api/wham/rate-limit-reset-credits`.
- Query current Codex usage windows from `https://chatgpt.com/backend-api/wham/usage`.
- Write sanitized snapshots under `$CODEX_HOME\status_snapshots\reset_credit_monitor`.
- Explain history changes from local JSONL snapshots.
- Generate local wrapper scripts for Windows Task Scheduler.
- Install, inspect, run, or remove the Windows Scheduled Task `CodexResetCreditMonitor`.

## Safety Rules

- Do not print tokens, raw `auth.json`, mailbox address, user id, or account id.
- Treat the backend request as read-only; never redeem reset credits.
- Prefer a 6-hour task interval unless the user explicitly asks otherwise.
- Accept user-defined intervals with `--hours N` or duration expressions such as `10h`, `1d`, `10hours`, `10小时`; allowed range is 1 to 168 hours.
- Do not use Codex automations for periodic polling unless the user explicitly requests that; Windows Task Scheduler avoids model/token usage.

## Output Files

Default output directory:

```text
$CODEX_HOME\status_snapshots\reset_credit_monitor
```

Files:

- `latest.json`: latest sanitized snapshot.
- `history.jsonl`: append-only sanitized snapshot history.
- `monitor.log`: task execution log lines.
- `task\run_monitor.cmd`: wrapper script executed by Windows Task Scheduler.
- `task\install_task.ps1`: generated install helper.
- `task\remove_task.ps1`: generated remove helper.
- `task\task_config.json`: generated task configuration metadata.
