# Codex Status Check

`codex-status-check` is a Codex skill for checking Codex update information from an upgrade-oriented perspective.

It focuses on one question: after a new Codex version appears and you update, what changed compared with the version currently installed on this machine?

## Features

- Reads the current local Codex CLI/App version from the local Codex environment.
- Reads the current Windows Codex desktop Appx package version when available.
- Scans recent local Codex desktop logs for app package versions, internal desktop release values, app-server CLI versions, and bundled CLI paths.
- Fetches official Codex product updates from the OpenAI Developers changelog RSS.
- Fetches engineering releases from `openai/codex` GitHub releases.
- Separates releases that are relevant to the current CLI channel from unrelated alpha/stable channel updates.
- Uses GitHub compare patches to explain the upgrade diff from the current CLI version to the newer version.
- Expands upgrade details into commit title, extracted summary, inferred impact, and changed-file scope when available.

## Install

Copy this repository into your Codex skills directory:

```powershell
$skillRoot = Join-Path $env:CODEX_HOME "skills\codex-status-check"
Copy-Item -Recurse -Force . $skillRoot
```

If `CODEX_HOME` is not set, use your Codex home directory, usually:

```text
~/.codex/skills/codex-status-check
```

## Usage

Invoke the skill in Codex:

```text
$codex-status-check
```

You can also ask naturally:

```text
查看 Codex 当前版本和可升级版本的更新内容
```

For local debugging, run the helper script:

```powershell
python "$env:CODEX_HOME\skills\codex-status-check\scripts\codex_status_check.py" updates --count 3
```

## Output

The report includes:

- Current machine Codex version information.
- Local desktop app status and recent version signals from Codex desktop logs.
- Version relevance baseline, usually the configured local CLI version.
- GitHub releases relevant to the current CLI channel and version.
- Upgrade compare link from the current version to the target version.
- Detailed upgrade differences, including summary, impact, and changed-file scope.
- Official Codex product updates, shown separately because they are not filtered by local CLI version.
- Latest GitHub engineering releases from other channels for reference.

## Data Sources

- OpenAI Codex changelog RSS: `https://developers.openai.com/codex/changelog/rss.xml`
- GitHub releases: `https://github.com/openai/codex/releases.atom`
- GitHub compare patches: `https://github.com/openai/codex/compare/<base>...<head>.patch`
- Local Windows package metadata from `Get-AppxPackage OpenAI.Codex`.
- Local desktop logs under `%LOCALAPPDATA%\Codex\Logs`.
- X/Twitter search URL is provided for optional manual cross-checking.

## Privacy Notes

The skill reads local Codex metadata to determine installed versions. Desktop log entries are machine-local evidence that an app package or runtime changed; they are not official release notes and should not be used to infer user-visible changes without a matching changelog or release entry.

It does not publish local paths, account information, or usage data by itself. When sharing output publicly, review the version and desktop status blocks and remove any local executable paths if present.

This repository intentionally excludes local caches such as `__pycache__`, SQLite state files, and machine-specific Codex configuration.

## Repository Layout

```text
codex-status-check/
  SKILL.md
  agents/
    openai.yaml
  scripts/
    codex_status_check.py
```
