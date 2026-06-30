---
name: codex-status-check
description: Query recent Codex update logs and summarize what changed using official OpenAI Codex changelog, GitHub releases, GitHub compare patches, and an optional X/Twitter search entry. Use when the user asks to view recent Codex updates, Codex release notes, Codex changelog content, or the current machine's Codex version.
---

# Codex Status Check

Use this skill for Codex update lookup.

## Quick Start

Call this skill from Codex:

```text
$codex-status-check
```

Run the helper script directly after installing the skill:

```powershell
python "$env:CODEX_HOME\skills\codex-status-check\scripts\codex_status_check.py" updates --count 3
```

If `CODEX_HOME` is not set, replace it with your Codex home directory, usually `~/.codex`.

The script output includes:

- Current machine Codex version information from local Codex config, `codex --version`, and the latest local thread metadata.
- A relevance baseline based on the current configured CLI version when available.
- GitHub releases that are relevant to the current CLI channel and version, including upgrade compare details from the current version to the newer version.
- Detailed upgrade entries with commit title, extracted summary, inferred impact, and changed-file scope when compare data supports it.
- Official product updates from `https://developers.openai.com/codex/changelog/rss.xml`.
- GitHub engineering release updates from `https://github.com/openai/codex/releases.atom`.
- GitHub compare summaries when release notes are too brief or explicitly say there are no user-facing changes.
- An X/Twitter search URL for optional manual cross-checking.

## Output Rules

- Prefer official Codex changelog RSS for product-facing update summaries.
- Use GitHub releases and compare patches for engineering-level details.
- Separate current-version-relevant GitHub updates from general latest releases.
- For current-version-relevant updates, summarize the diff from the installed/current CLI version to the target version so the user can understand what changed after updating.
- Prefer detailed, reader-facing upgrade explanations over terse release-note text when compare data is available.
- Treat official product changelog items as product news that is not filtered by local CLI version.
- Do not infer user-visible changes from empty release notes unless compare data supports the summary.
