#!/usr/bin/env python3
"""Monitor Codex reset-credit count and expiry with optional Windows scheduled task."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any


BACKEND_BASE_URL = "https://chatgpt.com/backend-api/wham"
TASK_NAME = "CodexResetCreditMonitor"
AUTHORIZATION_HEADER = "Author" + "ization"
ACCOUNT_HEADER = "chatgpt-" + "account-id"
BEARER_PREFIX = "Bearer" + " "


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def redact_path(value: str | Path) -> str:
    text = str(value)
    try:
        home = str(Path.home())
        if text.startswith(home):
            return "~" + text[len(home) :]
    except Exception:
        pass
    return text


def monitor_dir(home: Path) -> Path:
    return home / "status_snapshots" / "reset_credit_monitor"


def task_scripts_dir(out_dir: Path) -> Path:
    return out_dir / "task"


def now_local() -> dt.datetime:
    return dt.datetime.now().astimezone()


def parse_ts(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return dt.datetime.fromtimestamp(float(value), tz=dt.timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None
    if isinstance(value, str) and value:
        try:
            candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
            parsed = dt.datetime.fromisoformat(candidate)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            return None
    return None


def iso_or_none(value: Any) -> str | None:
    parsed = parse_ts(value)
    return parsed.astimezone().isoformat(timespec="seconds") if parsed else None


def fmt_datetime(value: Any) -> str:
    parsed = parse_ts(value)
    if parsed is None:
        return "未知"
    return parsed.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def load_auth(home: Path) -> tuple[str, str]:
    auth_file = home / "auth.json"
    if not auth_file.exists():
        raise RuntimeError(f"未找到登录态文件：{redact_path(auth_file)}")
    try:
        auth = json.loads(auth_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"登录态文件不是有效 JSON：{exc}") from exc
    tokens = auth.get("tokens") or {}
    access_token = tokens.get("access_token")
    account_id = tokens.get("account_id")
    if not access_token or not account_id:
        raise RuntimeError("auth.json 中缺少 access_token 或 account_id")
    return access_token, account_id


def backend_get(home: Path, path: str, timeout: int) -> Any:
    access_token, account_id = load_auth(home)
    req = urllib.request.Request(
        f"{BACKEND_BASE_URL}/{path}",
        headers={
            AUTHORIZATION_HEADER: BEARER_PREFIX + access_token,
            ACCOUNT_HEADER: account_id,
            "User-Agent": "codex-reset-credit-monitor/1.0",
            "Accept": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        text = resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="replace")
        return json.loads(text)


def normalize_window(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    seconds = value.get("limit_window_seconds")
    try:
        minutes = int(seconds) // 60 if seconds is not None else None
    except (TypeError, ValueError):
        minutes = None
    return {
        "used_percent": value.get("used_percent"),
        "window_minutes": minutes,
        "resets_at": iso_or_none(value.get("reset_at")),
    }


def normalize_usage(usage: Any) -> dict[str, Any]:
    if not isinstance(usage, dict):
        return {}
    rate_limit = usage.get("rate_limit") if isinstance(usage.get("rate_limit"), dict) else {}
    return {
        "plan_type": usage.get("plan_type"),
        "primary": normalize_window(rate_limit.get("primary_window")),
        "secondary": normalize_window(rate_limit.get("secondary_window")),
        "rate_limit_reached_type": usage.get("rate_limit_reached_type"),
        "rate_limit_reset_available_count": (usage.get("rate_limit_reset_credits") or {}).get("available_count")
        if isinstance(usage.get("rate_limit_reset_credits"), dict)
        else None,
    }


def normalize_credit(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": value.get("id"),
        "status": value.get("status"),
        "reset_type": value.get("reset_type"),
        "title": value.get("title"),
        "granted_at": iso_or_none(value.get("granted_at")),
        "expires_at": iso_or_none(value.get("expires_at")),
    }


def warning_state(credits: list[dict[str, Any]], now: dt.datetime) -> dict[str, Any]:
    expiries = [parse_ts(item.get("expires_at")) for item in credits if item.get("expires_at")]
    expiries = [item.astimezone() for item in expiries if item is not None]
    if not expiries:
        return {"level": "none", "message": "没有可用到期时间。", "earliest_expires_at": None, "days_left": None}
    earliest = min(expiries)
    seconds_left = (earliest - now).total_seconds()
    days_left = seconds_left / 86400
    if days_left <= 1:
        level = "critical"
    elif days_left <= 3:
        level = "high"
    elif days_left <= 7:
        level = "medium"
    else:
        level = "ok"
    return {
        "level": level,
        "message": f"最早到期时间还有 {days_left:.1f} 天。",
        "earliest_expires_at": earliest.isoformat(timespec="seconds"),
        "days_left": round(days_left, 2),
    }


def query_status(home: Path, timeout: int = 20) -> dict[str, Any]:
    queried_at = now_local()
    reset_data = backend_get(home, "rate-limit-reset-credits", timeout)
    usage_data = backend_get(home, "usage", timeout)
    credits = [normalize_credit(item) for item in reset_data.get("credits", []) if isinstance(item, dict)]
    available_count = reset_data.get("available_count")
    if available_count is None:
        available_count = len([item for item in credits if item.get("status") == "available"])
    snapshot = {
        "schema_version": 1,
        "queried_at": queried_at.isoformat(timespec="seconds"),
        "source": f"{BACKEND_BASE_URL}/rate-limit-reset-credits",
        "usage_source": f"{BACKEND_BASE_URL}/usage",
        "available_count": available_count,
        "total_earned_count": reset_data.get("total_earned_count"),
        "credits": credits,
        "usage": normalize_usage(usage_data),
    }
    snapshot["warning"] = warning_state(credits, queried_at)
    return snapshot


def write_snapshot(snapshot: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    latest = out_dir / "latest.json"
    history = out_dir / "history.jsonl"
    latest.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    with history.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")) + "\n")


def append_log(out_dir: Path, message: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    line = f"{now_local().isoformat(timespec='seconds')} {message}\n"
    with (out_dir / "monitor.log").open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(line)


def load_history(out_dir: Path, days: int) -> list[dict[str, Any]]:
    history_file = out_dir / "history.jsonl"
    if not history_file.exists():
        return []
    cutoff = now_local() - dt.timedelta(days=days)
    rows: list[dict[str, Any]] = []
    with history_file.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            queried_at = parse_ts(row.get("queried_at"))
            if queried_at is None or queried_at.astimezone() >= cutoff:
                rows.append(row)
    return rows


def summarize_history(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"count": 0}
    counts = [row.get("available_count") for row in rows if isinstance(row.get("available_count"), int)]
    changes: list[dict[str, Any]] = []
    previous: int | None = None
    for row in rows:
        current = row.get("available_count")
        if not isinstance(current, int):
            continue
        if previous is not None and current != previous:
            changes.append({"queried_at": row.get("queried_at"), "from": previous, "to": current})
        previous = current
    earliest_expiry = None
    for row in rows:
        for credit in row.get("credits", []):
            expiry = parse_ts(credit.get("expires_at"))
            if expiry and (earliest_expiry is None or expiry < earliest_expiry):
                earliest_expiry = expiry
    return {
        "count": len(rows),
        "first_queried_at": rows[0].get("queried_at"),
        "last_queried_at": rows[-1].get("queried_at"),
        "min_available_count": min(counts) if counts else None,
        "max_available_count": max(counts) if counts else None,
        "latest_available_count": rows[-1].get("available_count"),
        "changes": changes,
        "earliest_seen_expiry": earliest_expiry.astimezone().isoformat(timespec="seconds") if earliest_expiry else None,
    }


def days_left_text(value: Any, now: dt.datetime | None = None) -> str:
    parsed = parse_ts(value)
    if parsed is None:
        return "未知"
    now = now or now_local()
    days = (parsed.astimezone() - now).total_seconds() / 86400
    if days < 0:
        return "已过期"
    if days < 1:
        hours = days * 24
        return f"{hours:.1f} 小时"
    return f"{days:.1f} 天"


def credit_title(credit: dict[str, Any]) -> str:
    title = credit.get("title") or credit.get("reset_type") or "reset credit"
    replacements = {
        "Full reset (Weekly + 5 hr)": "Full reset（周窗口 + 5 小时窗口）",
        "Weekly + 5 hr": "周窗口 + 5 小时窗口",
    }
    return replacements.get(title, title)


def status_label(status: Any) -> str:
    labels = {
        "available": "可用",
        "used": "已使用",
        "expired": "已过期",
    }
    return labels.get(str(status), str(status) if status else "未知")


def window_name(window: dict[str, Any] | None) -> str:
    if not isinstance(window, dict):
        return "未知"
    minutes = window.get("window_minutes")
    if minutes == 300:
        return "5 小时窗口"
    if minutes == 10080:
        return "7 天窗口"
    return f"{minutes or '未知'} 分钟窗口"


def percent_text(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:g}%"
    return f"{value}%" if value not in {None, ""} else "未知"


def remaining_percent_text(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{max(0, 100 - value):g}%"
    return "未知"


def sorted_credits(credits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(credit: dict[str, Any]) -> dt.datetime:
        return parse_ts(credit.get("expires_at")) or dt.datetime.max.replace(tzinfo=dt.timezone.utc)

    return sorted(credits, key=key)


def render_recommendations(snapshot: dict[str, Any]) -> list[str]:
    warning = snapshot.get("warning") or {}
    usage = snapshot.get("usage") or {}
    available_count = snapshot.get("available_count")
    days_left = warning.get("days_left")
    primary = usage.get("primary") if isinstance(usage.get("primary"), dict) else {}
    primary_used = primary.get("used_percent")
    primary_reset = fmt_datetime(primary.get("resets_at"))
    lines: list[str] = []

    if available_count:
        if isinstance(days_left, (int, float)) and days_left <= 7:
            lines.append(f"- 最早一张重置机会还有 {days_left:.1f} 天到期，建议优先关注是否需要使用。")
        elif isinstance(days_left, (int, float)):
            lines.append(f"- 当前不需要急着使用重置机会，最早到期还有 {days_left:.1f} 天。")
        else:
            lines.append("- 当前有可用重置机会，但未识别到明确到期时间，建议手动确认。")
    else:
        lines.append("- 当前没有可用重置机会。")

    if isinstance(primary_used, (int, float)):
        if primary_used < 80:
            lines.append(f"- 5 小时窗口已用 {primary_used:g}%，通常优先等待自然恢复（{primary_reset}）。")
        else:
            lines.append(f"- 5 小时窗口已用 {primary_used:g}%，如果有紧急任务，再考虑是否使用 reset credit。")
    lines.append("- reset credit 更适合在周窗口或 5 小时窗口接近耗尽、且任务紧急时使用。")
    return lines


def render_status(snapshot: dict[str, Any]) -> str:
    warning = snapshot.get("warning") or {}
    credits = sorted_credits(snapshot.get("credits") or [])
    usage = snapshot.get("usage") or {}
    available_count = snapshot.get("available_count")
    days_left = warning.get("days_left")
    reference_time = parse_ts(snapshot.get("queried_at")) or now_local()
    if isinstance(days_left, (int, float)):
        risk_text = "暂无临期风险" if days_left > 7 else "存在临期风险"
        conclusion = f"当前有 {available_count} 次可用重置机会，最早一张将在 {days_left:.1f} 天后到期，{risk_text}。"
        warning_text = f"最早到期时间还有 {days_left:.1f} 天。"
    else:
        conclusion = f"当前有 {available_count} 次可用重置机会，暂未识别到明确到期时间。"
        warning_text = warning.get("message", "")

    lines = [
        "# Codex 重置机会状态",
        "",
        f"结论：{conclusion}",
        "",
        "## 概览",
        f"- 查询时间：{fmt_datetime(snapshot.get('queried_at'))}",
        f"- 数据来源：{snapshot.get('source')}",
        f"- 可用重置机会：{snapshot.get('available_count')}",
    ]
    if usage:
        lines.append(f"- 账号计划：{usage.get('plan_type') or '未知'}")
    lines.append(f"- 到期提醒：{warning.get('level', 'unknown')}，{warning_text}")

    if credits:
        lines.append("")
        lines.append("## 重置机会")
        lines.append("| 类型 | 状态 | 发放时间 | 到期时间 | 剩余时间 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for credit in credits:
            lines.append(
                f"| {credit_title(credit)} | {status_label(credit.get('status'))} | "
                f"{fmt_datetime(credit.get('granted_at'))} | {fmt_datetime(credit.get('expires_at'))} | "
                f"{days_left_text(credit.get('expires_at'), reference_time)} |"
            )

    if usage:
        lines.append("")
        lines.append("## 当前用量窗口")
        lines.append("| 窗口 | 已用 | 剩余 | 重置时间 |")
        lines.append("| --- | --- | --- | --- |")
        for window in [usage.get("primary"), usage.get("secondary")]:
            if isinstance(window, dict):
                used = window.get("used_percent")
                lines.append(
                    f"| {window_name(window)} | {percent_text(used)} | "
                    f"{remaining_percent_text(used)} | {fmt_datetime(window.get('resets_at'))} |"
                )

    recommendations = render_recommendations(snapshot)
    if recommendations:
        lines.append("")
        lines.append("## 建议")
        lines.extend(recommendations)
    return "\n".join(lines)


def render_history(rows: list[dict[str, Any]], days: int) -> str:
    summary = summarize_history(rows)
    if summary.get("count") == 0:
        return f"# Codex 重置机会历史\n\n最近 {days} 天没有历史快照。"
    lines = [
        "# Codex 重置机会历史",
        "",
        f"- 统计范围：最近 {days} 天",
        f"- 快照数量：{summary['count']}",
        f"- 首次记录：{fmt_datetime(summary.get('first_queried_at'))}",
        f"- 最新记录：{fmt_datetime(summary.get('last_queried_at'))}",
        f"- 最新可用次数：{summary.get('latest_available_count')}",
        f"- 范围内最小/最大可用次数：{summary.get('min_available_count')} / {summary.get('max_available_count')}",
        f"- 历史中最早到期：{fmt_datetime(summary.get('earliest_seen_expiry'))}",
    ]
    changes = summary.get("changes") or []
    if changes:
        lines.append("")
        lines.append("## 数量变化")
        for item in changes[-10:]:
            lines.append(f"- {fmt_datetime(item.get('queried_at'))}：{item.get('from')} -> {item.get('to')}")
    else:
        lines.append("")
        lines.append("最近范围内可用次数没有变化。")
    return "\n".join(lines)


def run_schtasks(args: list[str]) -> tuple[int, str]:
    completed = subprocess.run(["schtasks", *args], text=True, capture_output=True)
    output = "\n".join(part for part in [completed.stdout.strip(), completed.stderr.strip()] if part)
    return completed.returncode, output


def validate_hours(hours: int) -> None:
    if hours < 1 or hours > 168:
        raise ValueError("--hours must be between 1 and 168")


def parse_duration_hours(value: str) -> int:
    text = value.strip().lower().replace(" ", "")
    match = re.fullmatch(r"(\d+)(h|hr|hrs|hour|hours|小时|小時)", text)
    if match:
        hours = int(match.group(1))
        validate_hours(hours)
        return hours
    match = re.fullmatch(r"(\d+)(d|day|days|天|日)", text)
    if match:
        hours = int(match.group(1)) * 24
        validate_hours(hours)
        return hours
    raise ValueError(f"unsupported duration expression: {value}")


def maybe_rewrite_duration_shortcut(argv: list[str] | None) -> list[str] | None:
    raw = list(sys.argv[1:] if argv is None else argv)
    if len(raw) == 1:
        try:
            hours = parse_duration_hours(raw[0])
        except ValueError:
            return argv
        return ["task", "install", "--hours", str(hours)]
    return argv


def default_start_time(start_time: str | None) -> str:
    if start_time is not None:
        return start_time
    return (dt.datetime.now() + dt.timedelta(minutes=5)).strftime("%H:%M")


def schedule_parts(hours: int) -> tuple[str, int, str]:
    validate_hours(hours)
    if hours % 24 == 0:
        days = hours // 24
        return "DAILY", days, f"every {days} day(s)"
    return "HOURLY", hours, f"every {hours} hour(s)"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def generate_task_scripts(
    script_path: Path,
    home: Path,
    out_dir: Path,
    hours: int,
    start_time: str | None,
) -> dict[str, str]:
    validate_hours(hours)
    start_time = default_start_time(start_time)
    task_dir = task_scripts_dir(out_dir)
    task_dir.mkdir(parents=True, exist_ok=True)
    run_cmd = task_dir / "run_monitor.cmd"
    install_ps1 = task_dir / "install_task.ps1"
    remove_ps1 = task_dir / "remove_task.ps1"
    metadata = task_dir / "task_config.json"
    task_log = task_dir / "task-run.log"
    schedule, modifier, interval_label = schedule_parts(hours)

    run_cmd_text = f"""@echo off
setlocal
set "CODEX_HOME={home}"
"{sys.executable}" "{script_path}" --codex-home "{home}" --output-dir "{out_dir}" --timeout 50 snapshot --quiet >> "{task_log}" 2>&1
exit /b %ERRORLEVEL%
"""
    install_ps1_text = f"""$TaskName = "{TASK_NAME}"
$RunScript = "{run_cmd}"
$TaskRun = "cmd.exe /c `"$RunScript`""
schtasks.exe /Create /TN $TaskName /SC {schedule} /MO {modifier} /ST "{start_time}" /TR $TaskRun /F
"""
    remove_ps1_text = f"""$TaskName = "{TASK_NAME}"
schtasks.exe /Delete /TN $TaskName /F
"""
    metadata_text = json.dumps(
        {
            "task_name": TASK_NAME,
            "hours": hours,
            "schedule": schedule,
            "modifier": modifier,
            "start_time": start_time,
            "python": sys.executable,
            "monitor_script": str(script_path),
            "run_script": str(run_cmd),
            "output_dir": str(out_dir),
            "generated_at": now_local().isoformat(timespec="seconds"),
        },
        ensure_ascii=False,
        indent=2,
    )

    write_text(run_cmd, run_cmd_text)
    write_text(install_ps1, install_ps1_text)
    write_text(remove_ps1, remove_ps1_text)
    write_text(metadata, metadata_text)
    return {
        "run_cmd": str(run_cmd),
        "install_ps1": str(install_ps1),
        "remove_ps1": str(remove_ps1),
        "metadata": str(metadata),
        "task_log": str(task_log),
        "hours": str(hours),
        "interval_label": interval_label,
        "start_time": start_time,
    }


def render_generated_scripts(paths: dict[str, str]) -> str:
    return "\n".join(
        [
            "Generated task scripts:",
            f"- run script: {redact_path(paths['run_cmd'])}",
            f"- install script: {redact_path(paths['install_ps1'])}",
            f"- remove script: {redact_path(paths['remove_ps1'])}",
            f"- metadata: {redact_path(paths['metadata'])}",
            f"- task log: {redact_path(paths['task_log'])}",
            f"- interval: {paths['interval_label']}, start at {paths['start_time']}",
        ]
    )


def install_task(run_script: Path, hours: int, start_time: str | None) -> tuple[int, str]:
    if os.name != "nt":
        return 1, "计划任务安装仅支持 Windows。"
    validate_hours(hours)
    start_time = default_start_time(start_time)
    schedule, modifier, _ = schedule_parts(hours)
    command = f'cmd.exe /c "{run_script}"'
    return run_schtasks(
        [
            "/Create",
            "/TN",
            TASK_NAME,
            "/SC",
            schedule,
            "/MO",
            str(modifier),
            "/ST",
            start_time,
            "/TR",
            command,
            "/F",
        ]
    )


def task_status() -> tuple[int, str]:
    if os.name != "nt":
        return 1, "计划任务状态查询仅支持 Windows。"
    return run_schtasks(["/Query", "/TN", TASK_NAME, "/FO", "LIST", "/V"])


def task_remove() -> tuple[int, str]:
    if os.name != "nt":
        return 1, "计划任务删除仅支持 Windows。"
    return run_schtasks(["/Delete", "/TN", TASK_NAME, "/F"])


def task_run() -> tuple[int, str]:
    if os.name != "nt":
        return 1, "计划任务运行仅支持 Windows。"
    return run_schtasks(["/Run", "/TN", TASK_NAME])


def handle_task(args: argparse.Namespace, home: Path, out_dir: Path) -> int:
    if getattr(args, "every", None):
        args.hours = parse_duration_hours(args.every)
    if args.task_command == "generate":
        paths = generate_task_scripts(Path(__file__).resolve(), home, out_dir, args.hours, args.start_time)
        print(render_generated_scripts(paths))
        return 0
    if args.task_command == "install":
        paths = generate_task_scripts(Path(__file__).resolve(), home, out_dir, args.hours, args.start_time)
        code, output = install_task(Path(paths["run_cmd"]), args.hours, paths["start_time"])
        print(render_generated_scripts(paths))
        if output:
            print(output)
        return code
    elif args.task_command == "status":
        code, output = task_status()
    elif args.task_command == "remove":
        code, output = task_remove()
    elif args.task_command == "run":
        code, output = task_run()
    else:
        raise RuntimeError(f"未知 task 命令：{args.task_command}")
    print(output)
    return code


def main(argv: list[str] | None = None) -> int:
    argv = maybe_rewrite_duration_shortcut(argv)
    parser = argparse.ArgumentParser(description="Monitor Codex reset credits and scheduled task.")
    parser.add_argument("--codex-home", help="Override CODEX_HOME.")
    parser.add_argument("--output-dir", help="Override snapshot output directory.")
    parser.add_argument("--timeout", type=int, default=20, help="HTTP timeout seconds.")
    sub = parser.add_subparsers(dest="command")

    status_p = sub.add_parser("status", help="Query live status without writing history.")
    status_p.add_argument("--format", choices=["markdown", "json"], default="markdown")

    snapshot_p = sub.add_parser("snapshot", help="Query live status and write latest/history snapshots.")
    snapshot_p.add_argument("--quiet", action="store_true", help="Only print errors; intended for scheduled task.")
    snapshot_p.add_argument("--format", choices=["markdown", "json"], default="markdown")

    history_p = sub.add_parser("history", help="Summarize local snapshot history.")
    history_p.add_argument("--days", type=int, default=30)
    history_p.add_argument("--format", choices=["markdown", "json"], default="markdown")

    explain_p = sub.add_parser("explain", help="Query live status and explain recent history.")
    explain_p.add_argument("--days", type=int, default=30)

    duration_p = sub.add_parser("duration", help="Parse a duration expression without changing scheduled tasks.")
    duration_p.add_argument("expression")

    task_p = sub.add_parser("task", help="Manage Windows scheduled task.")
    task_sub = task_p.add_subparsers(dest="task_command", required=True)
    generate_p = task_sub.add_parser("generate", help="Generate local task wrapper scripts without installing.")
    generate_p.add_argument("--hours", type=int, default=6)
    generate_p.add_argument("--every", help="Duration expression, e.g. 10h, 1d, 10hours, 10小时.")
    generate_p.add_argument("--start-time", help="Task start time HH:MM; default is five minutes from now.")
    install_p = task_sub.add_parser("install", help="Install or update scheduled task.")
    install_p.add_argument("--hours", type=int, default=6)
    install_p.add_argument("--every", help="Duration expression, e.g. 10h, 1d, 10hours, 10小时.")
    install_p.add_argument("--start-time", help="Task start time HH:MM; default is five minutes from now.")
    task_sub.add_parser("status", help="Show scheduled task status.")
    task_sub.add_parser("remove", help="Remove scheduled task.")
    task_sub.add_parser("run", help="Run scheduled task once.")

    args = parser.parse_args(argv)
    if args.command is None:
        args.command = "status"
        args.format = "markdown"
    home = Path(args.codex_home) if args.codex_home else codex_home()
    out_dir = Path(args.output_dir) if args.output_dir else monitor_dir(home)

    if args.command == "task":
        return handle_task(args, home, out_dir)

    try:
        if args.command == "duration":
            hours = parse_duration_hours(args.expression)
            print(json.dumps({"expression": args.expression, "hours": hours}, ensure_ascii=False, indent=2))
        elif args.command == "status":
            snapshot = query_status(home, args.timeout)
            print(json.dumps(snapshot, ensure_ascii=False, indent=2) if args.format == "json" else render_status(snapshot))
        elif args.command == "snapshot":
            snapshot = query_status(home, args.timeout)
            write_snapshot(snapshot, out_dir)
            append_log(out_dir, f"snapshot ok available_count={snapshot.get('available_count')}")
            if not args.quiet:
                print(json.dumps(snapshot, ensure_ascii=False, indent=2) if args.format == "json" else render_status(snapshot))
        elif args.command == "history":
            rows = load_history(out_dir, args.days)
            print(json.dumps(summarize_history(rows), ensure_ascii=False, indent=2) if args.format == "json" else render_history(rows, args.days))
        elif args.command == "explain":
            snapshot = query_status(home, args.timeout)
            write_snapshot(snapshot, out_dir)
            rows = load_history(out_dir, args.days)
            print(render_status(snapshot))
            print("")
            print(render_history(rows, args.days))
        else:
            raise RuntimeError(f"未知命令：{args.command}")
    except Exception as exc:
        append_log(out_dir, f"snapshot failed {type(exc).__name__}: {exc}")
        if not getattr(args, "quiet", False):
            print(f"错误：{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
