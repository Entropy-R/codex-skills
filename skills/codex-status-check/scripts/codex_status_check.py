#!/usr/bin/env python3
"""Query recent Codex updates from official and GitHub sources."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


CODEX_CHANGELOG_RSS_URL = "https://developers.openai.com/codex/changelog/rss.xml"
GITHUB_RELEASES_ATOM_URL = "https://github.com/openai/codex/releases.atom"
GITHUB_COMPARE_URL = "https://github.com/openai/codex/compare/{base}...{head}"
X_CODEX_SEARCH_URL = "https://x.com/search?q=Codex%20(from%3AOpenAI%20OR%20from%3AOpenAIDevs)&src=typed_query&f=live"
DESKTOP_LOG_VERSION_DAYS = 14


class HTMLText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"br", "p", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        value = html.unescape("".join(self.parts))
        lines = [re.sub(r"\s+", " ", line).strip() for line in value.splitlines()]
        return "\n".join(line for line in lines if line)


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def local_app_data() -> Path:
    return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")


def redact_path(value: str) -> str:
    if not value:
        return value
    try:
        text = str(Path(value))
        replacements = [
            (str(Path.home()), "~"),
            (os.environ.get("LOCALAPPDATA") or "", "%LOCALAPPDATA%"),
            (os.environ.get("APPDATA") or "", "%APPDATA%"),
            (os.environ.get("ProgramFiles") or "", "%ProgramFiles%"),
            (os.environ.get("ProgramFiles(x86)") or "", "%ProgramFiles(x86)%"),
        ]
        for prefix, replacement in replacements:
            if prefix and text.lower().startswith(prefix.lower()):
                return replacement + text[len(prefix) :]
        if re.match(r"^[A-Za-z]:\\", text):
            return "<local-drive>" + text[2:]
        return text
    except Exception:
        return value


def fetch_text(url: str, timeout: int = 25) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "codex-update-check/1.0",
            "Accept": "application/rss+xml,application/atom+xml,text/x-patch,text/html;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode(resp.headers.get_content_charset() or "utf-8", errors="replace")


def html_to_text(value: str) -> str:
    parser = HTMLText()
    parser.feed(value or "")
    return parser.text()


def current_versions(home: Path) -> dict[str, str]:
    versions: dict[str, str] = {}
    config = home / "config.toml"
    if config.exists():
        text = config.read_text(encoding="utf-8", errors="replace")
        app_version = re.search(r'BROWSER_USE_CODEX_APP_VERSION\s*=\s*"([^"]+)"', text)
        cli_path = re.search(r"CODEX_CLI_PATH\s*=\s*'([^']+)'", text)
        if app_version:
            versions["codex_app_version"] = app_version.group(1)
        if cli_path:
            versions["configured_cli_path"] = redact_path(cli_path.group(1))
            versions["configured_cli_version"] = run_version([cli_path.group(1), "--version"])

    codex_command = shutil.which("codex") or shutil.which("codex.cmd")
    if codex_command:
        versions["path_codex_command"] = redact_path(codex_command)
        versions["path_codex_version"] = run_version([codex_command, "--version"], shell=codex_command.lower().endswith(".cmd"))

    db = home / "state_5.sqlite"
    if db.exists():
        try:
            with sqlite3.connect(str(db)) as conn:
                row = conn.execute(
                    "select cli_version from threads where cli_version <> '' order by updated_at desc limit 1"
                ).fetchone()
                if row:
                    versions["latest_thread_cli_version"] = row[0]
        except sqlite3.Error:
            pass
    return versions


def current_desktop_package() -> dict[str, str]:
    """Read the Windows Store/Appx desktop package version when available."""
    if sys.platform != "win32":
        return {}
    command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        (
            "$pkg = Get-AppxPackage -Name OpenAI.Codex -ErrorAction SilentlyContinue; "
            "if ($pkg) { "
            "$pkg | Select-Object Name,PackageFullName,Version,InstallLocation,Status "
            "| ConvertTo-Json -Compress "
            "}"
        ),
    ]
    try:
        output = subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL, timeout=8).strip()
    except Exception:
        return {}
    if not output:
        return {}
    try:
        import json

        data = json.loads(output)
    except Exception:
        return {}
    if isinstance(data, list):
        data = data[0] if data else {}
    return {
        "name": str(data.get("Name") or ""),
        "package_full_name": str(data.get("PackageFullName") or ""),
        "version": str(data.get("Version") or ""),
        "install_location": redact_path(str(data.get("InstallLocation") or "")),
        "status": str(data.get("Status") or ""),
    }


def desktop_log_dirs(days: int = DESKTOP_LOG_VERSION_DAYS) -> list[Path]:
    root = local_app_data() / "Codex" / "Logs"
    if not root.exists():
        return []
    today = dt.datetime.now().date()
    dirs: list[Path] = []
    for offset in range(days):
        day = today - dt.timedelta(days=offset)
        candidate = root / f"{day:%Y}" / f"{day:%m}" / f"{day:%d}"
        if candidate.exists():
            dirs.append(candidate)
    return dirs


def desktop_log_versions(days: int = DESKTOP_LOG_VERSION_DAYS) -> list[dict[str, str]]:
    """Extract desktop package and internal release versions seen in recent desktop logs."""
    records: dict[tuple[str, str, str], dict[str, str]] = {}
    package_pattern = re.compile(r"OpenAI\.Codex_(\d+\.\d+\.\d+\.0)")
    release_pattern = re.compile(r"\brelease=(\d+\.\d+\.\d+)\b")
    app_server_pattern = re.compile(r"Current reported app-server version: currentVersion=([^\s]+)")
    cli_path_pattern = re.compile(r"codexCliPath=([^\s]+codex\.exe)")
    cutoff = dt.datetime.now() - dt.timedelta(days=days)

    for directory in desktop_log_dirs(days):
        for log_file in sorted(directory.glob("*.log")):
            try:
                stat = log_file.stat()
            except OSError:
                continue
            modified = dt.datetime.fromtimestamp(stat.st_mtime)
            if modified < cutoff:
                continue
            try:
                text = log_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            snippets = [
                ("desktop_package", package_pattern),
                ("internal_release", release_pattern),
                ("app_server", app_server_pattern),
                ("bundled_cli_path", cli_path_pattern),
            ]
            for kind, pattern in snippets:
                for match in pattern.finditer(text):
                    value = match.group(1).strip().strip('"')
                    if kind == "bundled_cli_path":
                        value = redact_path(value)
                    key = (kind, value, directory.name)
                    existing = records.get(key)
                    if not existing or modified > dt.datetime.fromisoformat(existing["last_seen_iso"]):
                        records[key] = {
                            "kind": kind,
                            "value": value,
                            "log_date": directory.name,
                            "last_seen": modified.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
                            "last_seen_iso": modified.isoformat(),
                            "log_file": redact_path(str(log_file)),
                        }

    return sorted(records.values(), key=lambda item: (item["last_seen_iso"], item["kind"], item["value"]), reverse=True)


def parse_codex_version(value: str | None) -> tuple[int, int, int, str | None, int | None] | None:
    if not value:
        return None
    match = re.search(r"(\d+)\.(\d+)\.(\d+)(?:-([a-z]+)\.(\d+))?", value)
    if not match:
        return None
    pre_name = match.group(4)
    pre_number = int(match.group(5)) if match.group(5) else None
    return int(match.group(1)), int(match.group(2)), int(match.group(3)), pre_name, pre_number


def version_label(version: tuple[int, int, int, str | None, int | None]) -> str:
    major, minor, patch, pre_name, pre_number = version
    base = f"{major}.{minor}.{patch}"
    return f"{base}-{pre_name}.{pre_number}" if pre_name and pre_number is not None else base


def version_tag(version: tuple[int, int, int, str | None, int | None]) -> str:
    return f"rust-v{version_label(version)}"


def version_sort_key(version: tuple[int, int, int, str | None, int | None]) -> tuple[int, int, int, int, int]:
    major, minor, patch, pre_name, pre_number = version
    # Stable releases sort after pre-releases for the same base version.
    return major, minor, patch, 1 if pre_name is None else 0, pre_number or 0


def version_channel(version: tuple[int, int, int, str | None, int | None]) -> str:
    return "alpha" if version[3] == "alpha" else "stable"


def primary_cli_version(versions: dict[str, str]) -> dict[str, str] | None:
    candidates = [
        ("configured_cli_version", "配置中的 CLI"),
        ("latest_thread_cli_version", "最近线程 CLI"),
        ("path_codex_version", "PATH 中的 CLI"),
    ]
    for key, label in candidates:
        parsed = parse_codex_version(versions.get(key))
        if parsed:
            return {"source": label, "raw": versions[key], "version": version_label(parsed)}
    return None


def current_cli_tuple(versions: dict[str, str]) -> tuple[int, int, int, str | None, int | None] | None:
    primary = primary_cli_version(versions)
    return parse_codex_version(primary["version"]) if primary else None


def run_version(command: list[str], shell: bool = False) -> str:
    try:
        output = subprocess.check_output(command, text=True, stderr=subprocess.STDOUT, timeout=5, shell=shell)
        return output.strip()
    except Exception as exc:
        return f"获取失败：{type(exc).__name__}"


def parse_product_rss(rss_text: str) -> list[dict[str, str]]:
    root = ET.fromstring(rss_text)
    content_ns = "{http://purl.org/rss/1.0/modules/content/}"
    items: list[dict[str, str]] = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        body = item.findtext(f"{content_ns}encoded") or item.findtext("description") or ""
        items.append(
            {
                "title": title,
                "updated": pub_date,
                "url": link,
                "summary": summarize_text(html_to_text(body), max_items=5),
            }
        )
    return items


def parse_github_releases(atom_text: str) -> list[dict[str, Any]]:
    root = ET.fromstring(atom_text)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    releases: list[dict[str, Any]] = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
        updated = (entry.findtext("a:updated", default="", namespaces=ns) or "").strip()
        content_node = entry.find("a:content", ns)
        notes = html_to_text(content_node.text if content_node is not None else "")
        link_node = entry.find("a:link[@rel='alternate']", ns)
        url = link_node.attrib.get("href", "") if link_node is not None else ""
        releases.append(
            {
                "title": title,
                "updated": updated,
                "url": url,
                "tag": url.rstrip("/").split("/")[-1] if url else normalize_tag(title),
                "notes": notes,
                "summary": explain_release_notes(notes),
            }
        )
    attach_previous_tags(releases)
    for release in releases:
        enrich_github_release(release)
    return releases


def normalize_tag(value: str) -> str:
    value = value.strip()
    if value.startswith("rust-v"):
        return value
    if re.match(r"^\d+\.\d+\.\d+", value):
        return f"rust-v{value}"
    return value


def release_version(release: dict[str, Any]) -> tuple[int, int, int, str | None, int | None] | None:
    return parse_codex_version(release.get("tag") or release.get("title") or "")


def release_channel(tag: str) -> str:
    if "-alpha." in tag:
        return re.sub(r"\d+$", "", tag)
    match = re.match(r"^(rust-v\d+\.\d+\.)\d+$", tag)
    return match.group(1) if match else "other"


def attach_previous_tags(releases: list[dict[str, Any]]) -> None:
    for index, release in enumerate(releases):
        tag = normalize_tag(release["tag"])
        release["normalized_tag"] = tag
        release["previous_tag"] = None
        channel = release_channel(tag)
        for older in releases[index + 1 :]:
            older_tag = normalize_tag(older["tag"])
            if release_channel(older_tag) == channel:
                release["previous_tag"] = older_tag
                break


def release_notes_sparse(notes: str) -> bool:
    normalized = re.sub(r"\s+", " ", notes or "").strip()
    return not normalized or bool(re.fullmatch(r"Release\s+[\w.\-]+", normalized, flags=re.I))


def explain_release_notes(notes: str) -> str:
    normalized = re.sub(r"\s+", " ", notes or "").strip()
    if not normalized:
        return "该发布条目没有提供 release note 正文。"
    if re.search(r"no user-facing changes|no user facing changes|maintenance-only", normalized, re.I):
        return "维护发布：release note 明确说明没有用户可见变化。"
    if re.fullmatch(r"Release\s+[\w.\-]+", normalized, flags=re.I):
        return "自动发布条目，只记录版本发布，没有说明具体用户可见变化。"
    return summarize_text(notes, max_items=4)


def enrich_github_release(release: dict[str, Any]) -> None:
    if not release_notes_sparse(release.get("notes") or ""):
        return
    previous = release.get("previous_tag")
    current = release.get("normalized_tag")
    if not previous or not current:
        return
    commits, error = fetch_compare_commits(previous, current)
    if error:
        release["compare_error"] = error
    if commits:
        release["compare_url"] = GITHUB_COMPARE_URL.format(base=previous, head=current)
        release["commits"] = commits
        release["summary"] = summarize_commits(commits)


def fetch_compare_commits(base: str, head: str) -> tuple[list[dict[str, str]], str | None]:
    try:
        patch = fetch_text(GITHUB_COMPARE_URL.format(base=base, head=head) + ".patch", timeout=30)
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"
    return parse_patch_commits(patch), None


def parse_patch_commits(patch: str) -> list[dict[str, str]]:
    commits: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    body: list[str] = []
    in_headers = False

    def flush() -> None:
        nonlocal current, body
        if current:
            summary = extract_patch_summary(body)
            if summary:
                current["summary"] = summary
            files = extract_changed_files(body)
            if files:
                current["files"] = "；".join(files[:5])
            impact = infer_commit_impact(current, body)
            if impact:
                current["impact"] = impact
            if not skip_patch_commit(current, body):
                commits.append(current)
        current = None
        body = []

    for line in patch.splitlines():
        if line.startswith("From ") and line.endswith(" 2001"):
            flush()
            current = {"sha": line.split()[1][:7], "subject": ""}
            in_headers = True
            continue
        if current is None:
            continue
        if in_headers and line.startswith("Subject: "):
            current["subject"] = clean_subject(line[len("Subject: ") :])
            continue
        if in_headers and line.startswith(" ") and current.get("subject"):
            current["subject"] = clean_subject(current["subject"] + " " + line.strip())
            continue
        if in_headers and line == "---":
            body.append("---")
            in_headers = False
            continue
        if in_headers:
            if line.startswith(("From: ", "Date: ")) or not line.strip():
                continue
            body.append(line)
            continue
        if line.startswith("diff --git "):
            continue
        body.append(line)
    flush()
    return commits


def clean_subject(subject: str) -> str:
    subject = re.sub(r"^\[PATCH(?: \d+/\d+)?\]\s*", "", subject.strip())
    return re.sub(r"\s+", " ", subject)


def skip_patch_commit(commit: dict[str, str], body: list[str]) -> bool:
    subject = commit.get("subject", "").strip()
    if re.fullmatch(r"Release\s+[\w.\-]+", subject, flags=re.I):
        return True
    if subject.startswith("## Chores"):
        return True
    body_text = "\n".join(body)
    return bool(
        re.search(r"No user-facing changes were identified", body_text, re.I)
        and re.search(r"^\+version\s*=", body_text, re.M)
    )


def extract_patch_summary(lines: list[str]) -> str:
    captured: list[str] = []
    capture = False
    preamble_bullets: list[str] = []
    collecting_preamble = True
    saw_preamble = False
    for raw in lines:
        line = raw.strip()
        if line == "---":
            break
        if not capture and collecting_preamble and line.startswith("- "):
            bullet = line[2:].strip()
            if not re.search(r"^(just fmt|git diff --check|tests? not run)", bullet, re.I):
                preamble_bullets.append(bullet)
                saw_preamble = True
            if len(preamble_bullets) >= 4:
                break
            continue
        if (
            not capture
            and collecting_preamble
            and preamble_bullets
            and line
            and not line.startswith(("PR #", "## "))
            and re.search(r"(,\s*| or| and)$", preamble_bullets[-1])
        ):
            preamble_bullets[-1] = f"{preamble_bullets[-1]} {line}"
            continue
        if not capture and saw_preamble and line and not line.startswith("- "):
            collecting_preamble = False
        if line in {"## Summary", "## User impact", "## Impact", "## Why"}:
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.startswith("- "):
            captured.append(line[2:].strip())
        elif capture and line and not line.startswith(("---", "diff --git", "index ")):
            captured.append(line)
        if len(captured) >= 4:
            break
    return "；".join((captured or preamble_bullets)[:4])


def extract_changed_files(lines: list[str]) -> list[str]:
    files: list[str] = []
    for raw in lines:
        line = raw.rstrip()
        if line.startswith(("diff --git ", "index ", "--- a/", "+++ b/", "@@ ")):
            break
        if " | " not in line:
            continue
        path = line.split("|", 1)[0].strip()
        if path and not path[0].isdigit() and not path.startswith(("-", "+")) and path != "---":
            files.append(path)
    return files


def infer_commit_impact(commit: dict[str, str], lines: list[str]) -> str:
    subject = commit.get("subject", "")
    body = "\n".join(lines)
    if "Restore v1 delegation guidance" in subject:
        return (
            "更新后，v1 多代理工具说明会重新强调授权边界：用户要求深入、研究、彻底分析，不等于授权自动创建 subagent。"
            "它还要求先判断关键路径，把紧急、阻塞、强耦合任务留在主线程处理，把独立旁路任务交给子代理。"
        )
    if 'Revert "Make auto-review on-request prompt more proactive"' in subject:
        return (
            "更新后，auto_review 场景不再使用更主动的 on-request 权限提示模板，逻辑回到通用 on-request 提示路径。"
            "实际体感上，权限申请提示会少一些主动升级、网络/远程访问/沙箱预判类指导。"
        )
    if re.search(r"deleted file mode .*on_request_auto_review\.md", body):
        return "删除 auto_review 专用 on-request 权限提示模板，回到通用权限提示。"
    return ""


def summarize_commits(commits: list[dict[str, str]]) -> str:
    parts: list[str] = []
    for commit in commits[:5]:
        subject = commit.get("subject", "").strip()
        summary = commit.get("summary", "").strip()
        parts.append(f"{subject}：{summary}" if summary else subject)
    return "；".join(parts)


def format_commit_detail(commit: dict[str, str]) -> list[str]:
    subject = commit.get("subject", "").strip()
    summary = commit.get("summary", "").strip()
    impact = commit.get("impact", "").strip()
    files = commit.get("files", "").strip()
    lines = [f"    - {subject}"]
    if summary:
        lines.append(f"      摘要：{summary}")
    if impact:
        lines.append(f"      影响：{impact}")
    if files:
        lines.append(f"      涉及：{files}")
    return lines


def summarize_text(text: str, max_items: int) -> str:
    lines = [line.strip(" -*\t") for line in text.splitlines() if line.strip()]
    useful = [
        line
        for line in lines
        if not line.startswith("#")
        and not line.startswith("###")
        and not line.startswith("```")
        and not line.startswith("!")
        and not line.lower().startswith("full changelog")
    ]
    return "；".join(useful[:max_items]) or "未提供可提取摘要。"


def get_product_updates(count: int) -> tuple[list[dict[str, str]], str | None]:
    try:
        return parse_product_rss(fetch_text(CODEX_CHANGELOG_RSS_URL))[:count], None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def get_github_updates(count: int) -> tuple[list[dict[str, Any]], str | None]:
    try:
        return parse_github_releases(fetch_text(GITHUB_RELEASES_ATOM_URL))[:count], None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def annotate_release_relevance(releases: list[dict[str, Any]], current: tuple[int, int, int, str | None, int | None] | None) -> None:
    if not current:
        for release in releases:
            release["relevance"] = "无法判断：未识别到当前 CLI 版本。"
        return

    current_channel = version_channel(current)
    current_key = version_sort_key(current)
    for release in releases:
        parsed = release_version(release)
        if not parsed:
            release["relevance"] = "无法判断：未识别到该发布版本号。"
            continue
        release_channel_name = version_channel(parsed)
        if release_channel_name != current_channel:
            release["relevance"] = f"不同发布通道：当前使用 {current_channel}，该发布是 {release_channel_name}，通常只作参考。"
        elif version_sort_key(parsed) > current_key:
            release["relevance"] = "与你当前 CLI 同通道且更新，可作为升级相关版本。"
            enrich_upgrade_from_current(release, current)
        elif version_sort_key(parsed) == current_key:
            release["relevance"] = "与你当前 CLI 版本一致。"
        else:
            release["relevance"] = "早于你当前 CLI 版本。"


def enrich_upgrade_from_current(release: dict[str, Any], current: tuple[int, int, int, str | None, int | None]) -> None:
    target = release_version(release)
    if not target:
        return
    base_tag = version_tag(current)
    head_tag = normalize_tag(release.get("tag") or release.get("title") or version_tag(target))
    if base_tag == head_tag:
        return
    commits, error = fetch_compare_commits(base_tag, head_tag)
    release["upgrade_compare_url"] = GITHUB_COMPARE_URL.format(base=base_tag, head=head_tag)
    if error:
        release["upgrade_compare_error"] = error
        return
    release["upgrade_commits"] = commits
    if commits:
        release["upgrade_summary"] = summarize_commits(commits)


def related_github_updates(releases: list[dict[str, Any]], current: tuple[int, int, int, str | None, int | None] | None) -> list[dict[str, Any]]:
    if not current:
        return []
    current_channel = version_channel(current)
    current_key = version_sort_key(current)
    related: list[dict[str, Any]] = []
    for release in releases:
        parsed = release_version(release)
        if parsed and version_channel(parsed) == current_channel and version_sort_key(parsed) >= current_key:
            related.append(release)
    return related


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    home = Path(args.codex_home) if args.codex_home else codex_home()
    versions = current_versions(home)
    desktop_package = current_desktop_package()
    desktop_log_items = desktop_log_versions()
    product_updates, product_error = get_product_updates(args.count)
    github_updates, github_error = get_github_updates(args.count)
    current_cli = current_cli_tuple(versions)
    annotate_release_relevance(github_updates, current_cli)
    return {
        "generated_at": dt.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z"),
        "codex_home": redact_path(str(home)),
        "versions": versions,
        "desktop": {
            "package": desktop_package,
            "log_days": DESKTOP_LOG_VERSION_DAYS,
            "log_items": desktop_log_items,
        },
        "primary_cli_version": primary_cli_version(versions),
        "updates": {
            "product_source": CODEX_CHANGELOG_RSS_URL,
            "product_error": product_error,
            "product_items": product_updates,
            "github_source": GITHUB_RELEASES_ATOM_URL,
            "github_error": github_error,
            "github_items": github_updates,
            "github_related_items": related_github_updates(github_updates, current_cli),
            "x_search_url": X_CODEX_SEARCH_URL,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = ["# Codex 更新查询", "", f"- 生成时间：{payload['generated_at']}"]
    versions = payload.get("versions") or {}
    if versions:
        lines.append("- 当前机器 Codex 版本：")
        for key, value in versions.items():
            lines.append(f"  - {key}: {value}")
    primary = payload.get("primary_cli_version")
    if primary:
        lines.append(f"- 版本相关性判断基准：{primary['source']}（{primary['version']}）")

    desktop = payload.get("desktop") or {}
    package = desktop.get("package") or {}
    log_items = desktop.get("log_items") or []
    lines.extend(["", "## 本机桌面版状态与更新痕迹"])
    if package:
        lines.append(f"- 当前 Windows 桌面包：{package.get('package_full_name') or package.get('version')}")
        if package.get("install_location"):
            lines.append(f"  安装位置：{package['install_location']}")
    else:
        lines.append("- 未从 Windows Appx 包信息中识别到 OpenAI.Codex 桌面版。")
    if log_items:
        lines.append(f"- 最近 {desktop.get('log_days', DESKTOP_LOG_VERSION_DAYS)} 天桌面日志中捕捉到的版本信号：")
        for item in log_items[:12]:
            kind_label = {
                "desktop_package": "桌面包",
                "internal_release": "内部 release",
                "app_server": "App server/CLI",
                "bundled_cli_path": "随附 CLI 路径",
            }.get(item.get("kind"), item.get("kind", "unknown"))
            lines.append(
                f"  - {item.get('log_date')} {kind_label}: {item.get('value')}，最后出现：{item.get('last_seen')}"
            )
    else:
        lines.append(f"- 最近 {desktop.get('log_days', DESKTOP_LOG_VERSION_DAYS)} 天桌面日志中未提取到版本信号。")
    lines.append("- 说明：桌面日志只能证明本机安装包或运行时版本发生过变化；若官方 changelog 未发布对应条目，不推断用户可见变更。")

    updates = payload["updates"]
    lines.extend(["", "## 与当前 CLI 版本相关的 GitHub 更新"])
    related_items = updates.get("github_related_items", [])
    if updates.get("github_error"):
        lines.append(f"- 获取失败：{updates['github_error']}")
    elif not related_items:
        lines.append("- 未发现与当前 CLI 同通道且不早于当前版本的 GitHub 发布。")
    for item in related_items:
        lines.append(f"- {item['title']}（{item['updated']}）")
        lines.append(f"  关系：{item.get('relevance', '未判断')}")
        lines.append(f"  来源：{item['url']}")
        if item.get("upgrade_compare_url"):
            lines.append(f"  从当前版本升级对比：{item['upgrade_compare_url']}")
        elif item.get("compare_url"):
            lines.append(f"  变更对比：{item['compare_url']}")
        lines.append(f"  Release note：{item['summary']}")
        if item.get("upgrade_compare_error"):
            lines.append(f"  升级差异获取失败：{item['upgrade_compare_error']}")
        elif item.get("upgrade_commits"):
            lines.append("  升级差异明细：")
            for commit in item["upgrade_commits"]:
                lines.extend(format_commit_detail(commit))
        elif item.get("upgrade_compare_url"):
            lines.append("  升级差异明细：未从 compare patch 提取到非发布 commit。")

    lines.extend(["", "## 官方产品更新（不按本机 CLI 版本过滤）"])
    if updates.get("product_error"):
        lines.append(f"- 获取失败：{updates['product_error']}")
    for item in updates.get("product_items", []):
        lines.append(f"- {item['title']}（{item['updated']}）")
        lines.append(f"  来源：{item['url']}")
        lines.append(f"  内容：{item['summary']}")
    lines.append(f"- X/Twitter 检索入口：{updates['x_search_url']}")

    lines.extend(["", "## GitHub 最新工程发布（含其他通道，仅供参考）"])
    if updates.get("github_error"):
        lines.append(f"- 获取失败：{updates['github_error']}")
    for item in updates.get("github_items", []):
        lines.append(f"- {item['title']}（{item['updated']}）")
        lines.append(f"  关系：{item.get('relevance', '未判断')}")
        lines.append(f"  来源：{item['url']}")
        if item.get("compare_url"):
            lines.append(f"  变更对比：{item['compare_url']}")
        lines.append(f"  内容：{item['summary']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Query recent Codex updates.")
    parser.add_argument("command", nargs="?", choices=["updates"], default="updates", help="Query recent updates.")
    parser.add_argument("--count", type=int, default=3, help="Number of update entries to show per source.")
    parser.add_argument("--codex-home", help="Override CODEX_HOME.")
    args = parser.parse_args(argv)
    print(render_markdown(build_payload(args)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
