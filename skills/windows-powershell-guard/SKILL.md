---
name: windows-powershell-guard
description: "Guardrails for Codex when running commands or editing files on Windows PowerShell. Use when working in Windows shells, especially with Chinese paths or filenames, Chinese logs or script output, text encoding, JSON passed through PowerShell, quoting and escaping, path safety, deletion or move operations, cross-shell command composition, PowerShell startup failures, Python or Node scripts affected by Windows locale encodings, and repository maintenance where PowerShell behavior can corrupt text or affect unintended paths."
---

# Windows PowerShell 防护

## Overview

Use this skill to reduce common failures when Codex operates in Windows PowerShell, especially in repositories with Chinese paths, Chinese documents, logs, scripts, or mixed encodings. Communicate process updates in Chinese, but keep internal reasoning private: explain key ideas, decision basis, execution steps, validation results, and remaining risks.

This skill is not a permanent runtime switch by itself. If the user wants this behavior to apply by default across future Codex work, add a concise rule to the relevant `AGENTS.md` or the global Codex preferences file such as `$CODEX_HOME\AGENTS.md` or `~/.codex/AGENTS.md` that says to use `$windows-powershell-guard` for Windows PowerShell, Chinese encoding, path, deletion, and shell-command tasks.

## 核心原则

- Prefer the repository's existing style, scripts, tooling, and structure. Do not perform unrelated refactors while fixing a focused issue.
- Treat encoding, quoting, and path resolution as first-class risks on Windows. Verify assumptions before writing files, moving files, or deleting anything.
- Use `rg` or `rg --files` for search when available. Fall back only when needed.
- Use `apply_patch` for manual edits, especially for files containing Chinese text. Avoid writing Chinese content through `echo`, `Set-Content`, `Out-File`, or shell redirection unless encoding is explicit and verified.
- Keep user-facing explanations concise and in Chinese. Include public troubleshooting paths and validation results, not full hidden chain-of-thought.
- When this skill is active, treat it as the default command-safety layer for the current turn. Do not assume it will remain active in unrelated future turns unless `AGENTS.md` or the user request triggers it again.

## 命令执行规则

- Prefer native PowerShell commands end to end. Do not enumerate paths in PowerShell and then pass them to `cmd /c`, batch builtins, Bash, Python, or another shell for deletion, moving, or overwriting.
- Quote paths with `-LiteralPath` when paths may contain spaces, brackets, wildcards, Chinese characters, or other special characters.
- Use single quotes for literal PowerShell strings when interpolation is not needed.
- Avoid command chains that hide failure states. For multi-step checks, run clear, separate commands or a short PowerShell script block with explicit error handling.
- For JSON or structured input, prefer reading from files or here-strings handled by the target program. Avoid fragile inline JSON quoting through PowerShell unless the payload is small and verified.
- When running project scripts, inspect package files or existing docs first so the command matches local conventions.
- If PowerShell command execution fails before the command body runs, for example `CreateProcessWithLogonW failed: 1326`, treat it as a launcher, credential, sandbox, or shell-startup problem. Do not keep retrying the same command or misdiagnose it as a project-code failure; report the exact startup error and check the execution environment.

## 中文与编码规则

- Before editing Chinese text files, inspect existing encoding when feasible and preserve the file's style. Do not normalize encodings as an incidental change.
- Avoid these patterns for Chinese content unless explicit UTF-8 handling and verification are added:

```powershell
echo "中文" > file.txt
Set-Content file.txt "中文"
Out-File file.txt
```

- Prefer `apply_patch` for small and medium manual edits. For generated output that must be written by a script, specify UTF-8 explicitly and then verify by reading the file back.
- When capturing logs that may contain Chinese, prefer commands that preserve UTF-8 and verify the displayed text is not garbled before relying on it.
- If mojibake appears, stop and diagnose encoding instead of repeatedly rewriting the file.
- If Python scripts fail with `UnicodeDecodeError` on Windows because `Path.read_text()` or `open()` used the locale default encoding, identify whether the file or the validator expects UTF-8 or GBK. Prefer setting the script's encoding explicitly or running with UTF-8 mode when appropriate; if a legacy validator requires GBK, preserve that constraint and report it.

## 文件编辑规则

- Read the surrounding code or document structure before editing. Match naming, formatting, comment style, and existing language.
- Add concise Chinese comments only for complex logic, implicit business rules, or easy-to-misread boundaries.
- Keep edits scoped to the requested behavior. Do not rename directories, reorganize workflow materials, or change generated metadata unless the task requires it.
- When updating local Codex skills, keep the skill directory name and `name:` stable unless the user explicitly asks to rename the skill.
- For skill metadata, keep YAML frontmatter minimal and valid. `SKILL.md` frontmatter should contain only `name` and `description` unless the relevant skill creation rules say otherwise.

## 路径与删除安全

- Never batch-delete files or directories without explicit user confirmation.
- Before any recursive delete or bulk move, resolve and display the absolute target path, confirm it is inside the intended workspace or explicitly named target directory, and ask the user before proceeding.
- Prefer native PowerShell file operations with `-LiteralPath`, for example `Remove-Item -LiteralPath ...` or `Move-Item -LiteralPath ...`, only after the path safety check is complete.
- Do not use wildcard deletion for generated files in mixed project directories unless the exact target set has been reviewed.
- If unrelated user changes are present, leave them intact. Work with them only when they affect the requested task.

## PowerShell 常见坑

- `>` and `>>` may produce unexpected encodings depending on PowerShell version and environment. Avoid them for Chinese text and structured files.
- `Set-Content` and `Out-File` defaults vary by version. If they must be used, specify encoding intentionally and verify output.
- Unquoted paths can break on spaces and special characters; wildcard expansion can touch unintended files. Prefer `-LiteralPath`.
- Inline JSON often fails because PowerShell consumes quotes or escape characters. Prefer files, here-strings, or command-specific JSON input mechanisms.
- Some CLI examples assume Bash syntax. Translate environment variables, quoting, path separators, and command chaining into PowerShell semantics before running them.
- Do not mix shells for filesystem mutations. Cross-shell pipelines are acceptable only for read-only inspection when quoting is simple and the result is verified.
- Do not assume PowerShell 5.1 supports Bash-like `&&` and `||` semantics. Prefer separate commands or explicit `if ($LASTEXITCODE -eq 0) { ... }` blocks when compatibility matters.
- Use `Join-Path` or framework path APIs for constructed paths instead of manual string concatenation when paths may cross directories or contain Chinese characters.
- For `ConvertTo-Json`, set `-Depth` deliberately when objects are nested; shallow defaults can silently truncate useful data.
- If `pwsh.exe` resolves to a WindowsApps alias or another unavailable shim, a skill cannot fix the binary resolution. Check `Get-Command pwsh,powershell` and PATH ordering before blaming project commands.

## 验证要求

- After edits, run the smallest relevant validation: project tests, linters, build checks, or skill validation scripts.
- For encoding-sensitive changes, read the edited file back and check Chinese text renders correctly.
- For path-sensitive commands, report the resolved location or the exact file touched.
- In the final response, summarize in Chinese: changed files, validation command and result, remaining risk if any, and a concise Chinese commit message when code or skill files were modified.
