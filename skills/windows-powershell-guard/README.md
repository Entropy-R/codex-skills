# Windows PowerShell Guard

`windows-powershell-guard` 是一个用于降低 Codex 在 Windows PowerShell 环境中执行命令和编辑文件时常见失败的 Codex skill。

它重点约束中文路径、中文文件、中文日志、脚本输出编码、JSON 传参、路径安全、删除/移动文件、跨 shell 操作和 PowerShell 启动异常等场景，避免因为 PowerShell 默认编码、转义规则或路径展开导致文件损坏、命令失败或误操作。

## Usage

在 Codex 中直接调用：

```text
$windows-powershell-guard
```

常见用法：

```text
使用 $windows-powershell-guard，在 Windows PowerShell 下排查这个项目的命令执行失败问题
```

```text
使用 $windows-powershell-guard，处理中文路径、中文日志和编码相关问题
```

也可以把类似规则加入项目或全局 `AGENTS.md`，让后续 Windows PowerShell、中文编码、路径和文件操作默认按该 skill 的防护思路执行。

## What It Covers

- 避免用默认 `echo`、`Set-Content`、`Out-File` 或重定向直接写入中文内容。
- 优先使用 `apply_patch` 做手工编辑，降低中文编码损坏风险。
- 对路径使用 `-LiteralPath`，避免空格、通配符、中文字符或特殊字符导致误匹配。
- 不跨 shell 组合删除、移动、覆盖等文件系统操作。
- 批量删除或递归移动前要求解析绝对路径并征得用户确认。
- 对 JSON、PowerShell 引号和转义、`ConvertTo-Json -Depth`、PowerShell 5.1 兼容性提供约束。
- 对 `CreateProcessWithLogonW failed: 1326`、`pwsh.exe` alias、Windows locale 导致的 `UnicodeDecodeError` 等问题给出排查方向。

## Install

复制本目录到 Codex skills 目录：

```powershell
$source = ".\skills\windows-powershell-guard"
$target = Join-Path $env:CODEX_HOME "skills\windows-powershell-guard"
Copy-Item -Recurse -Force $source $target
```

如果没有设置 `CODEX_HOME`，通常可以复制到：

```text
~/.codex/skills/windows-powershell-guard
```

## Repository Layout

```text
windows-powershell-guard/
  README.md
  SKILL.md
  agents/
    openai.yaml
```
