# Codex Skills

这是我的个人 Codex skill 仓库，用来收集和自开发一些好用的 Codex skills。

每个 skill 都放在独立目录中，包含自己的 `SKILL.md`、脚本、配置和说明文档，方便按需安装、迁移和继续扩展。

## Repository Architecture

```text
codex-skills/
  README.md
  .gitignore
  skills/
    codex-status-check/
      README.md
      SKILL.md
      agents/
        openai.yaml
      scripts/
        codex_status_check.py
    codex-reset-credit-monitor/
      README.md
      SKILL.md
      agents/
        openai.yaml
      scripts/
        reset_credit_monitor.py
    windows-powershell-guard/
      README.md
      SKILL.md
      agents/
        openai.yaml
    codex-conversation-organizer/
      README.md
      SKILL.md
      agents/
        openai.yaml
      references/
      scripts/
        tests/
    requirement-intake/
      README.md
      SKILL.md
      agents/
        openai.yaml
    solution-design/
      README.md
      SKILL.md
      agents/
        openai.yaml
    solution-review/
      README.md
      SKILL.md
      agents/
        openai.yaml
    doc-source-analysis/
      README.md
      SKILL.md
      agents/
        openai.yaml
    doc-template-outline/
      README.md
      SKILL.md
      agents/
        openai.yaml
    doc-drafting/
      README.md
      SKILL.md
      agents/
        openai.yaml
    doc-format-check/
      README.md
      SKILL.md
      agents/
        openai.yaml
      assets/
        software-doc-format-template.md
    doc-content-proofread/
      README.md
      SKILL.md
      agents/
        openai.yaml
```

这个仓库采用聚合式结构：仓库根目录只放整体说明和通用配置，所有可用的 Codex skill 都放在 `skills/` 下。每个 skill 都是一个相对独立的单元，可以单独复制、安装和使用。

`skills/<skill-name>/SKILL.md` 是 Codex 识别 skill 的核心文件；`README.md` 用来说明该 skill 的用途和调用方式；`scripts/` 和 `agents/` 则按需存放辅助脚本和展示配置。

## Included Skills

| Skill | 调用方式 | 用途 |
| --- | --- | --- |
| `codex-status-check` | `$codex-status-check` | 查询当前 Codex 版本、同通道可升级版本、升级差异、官方产品更新和 GitHub 工程发布参考。 |
| `codex-reset-credit-monitor` | `$codex-reset-credit-monitor` | 查看 Codex reset credit 数量、到期时间、历史变化，并维护 Windows 计划任务监控。 |
| `windows-powershell-guard` | `$windows-powershell-guard` | 降低 Codex 在 Windows PowerShell、中文编码、路径操作和 shell 命令中的常见失败。 |
| `codex-conversation-organizer` | `$codex-conversation-organizer` | 按自然语言规则盘点、分类并迁移 Codex 对话的项目归属，默认保留原对话。 |
| `requirement-intake` | `$requirement-intake` | 三段开发 01：整理非结构化需求，主动澄清关键问题。 |
| `solution-design` | `$solution-design` | 三段开发 02：把澄清后的需求转换为工程实现方案。 |
| `solution-review` | `$solution-review` | 三段开发 03：审查方案风险并整理最终可执行计划。 |
| `doc-source-analysis` | `$doc-source-analysis` | 文档编写 01：解读技术协议和客户资料，提炼事实、术语、风险和待确认项。 |
| `doc-template-outline` | `$doc-template-outline` | 文档编写 02：适配客户模板并生成目录、大纲和章节写作说明。 |
| `doc-drafting` | `$doc-drafting` | 文档编写 03：基于大纲和资料解读结果起草正文。 |
| `doc-format-check` | `$doc-format-check` | 文档编写 04：按固定模板检查并统一文档格式。 |
| `doc-content-proofread` | `$doc-content-proofread` | 文档编写 05：对照参考资料校对事实、术语、逻辑和验收风险。 |

### codex-status-check

`codex-status-check` 用于查看当前机器上的 Codex 版本，并结合 OpenAI Codex changelog、GitHub releases 和 GitHub compare patch，说明从当前版本升级到新版本后实际发生了什么变化。

它会区分“与当前 CLI 版本相关的同通道更新”和“仅供参考的其它工程发布”，避免把 alpha/stable 等不同通道的更新混在一起。对于 release note 过于简略的版本，它会尝试读取 GitHub compare patch，补充 commit 摘要、影响说明和涉及文件范围。

### codex-reset-credit-monitor

`codex-reset-credit-monitor` 用于查看当前可用的 Codex reset credit 数量、每次机会的到期时间，以及当前 Codex 用量窗口。它可以记录本地快照历史，并根据历史数据解释 reset credit 数量变化和临期风险。

它还支持生成和维护 Windows 计划任务，用固定周期在本机记录 reset credit 状态。这个 skill 会读取本机 Codex 登录态并向 ChatGPT backend 发起只读请求，不调用模型，也不会输出 token、原始 `auth.json`、邮箱地址、user id 或 account id。

### windows-powershell-guard

`windows-powershell-guard` 用于约束 Codex 在 Windows PowerShell 下执行命令和编辑文件时的高风险行为，尤其是中文路径、中文文件、中文日志、脚本输出编码、JSON 传参、路径安全、删除/移动文件、跨 shell 操作和 shell 启动异常等场景。

它会提醒 Codex 优先使用 `apply_patch` 做手工编辑，避免默认 `echo`、`Set-Content`、`Out-File` 或重定向写中文内容；执行路径敏感操作时优先使用 `-LiteralPath` 并验证目标路径；遇到 `UnicodeDecodeError`、`CreateProcessWithLogonW failed: 1326`、`pwsh.exe` alias 等 Windows 环境问题时，先按环境和编码问题排查，而不是反复重跑同一命令。

### codex-conversation-organizer

`codex-conversation-organizer` 用于按照用户本次提供的自然语言规则整理已有 Codex 对话。它先盘点和分类，单独列出冲突与证据不足项；用户确认具体线程和目标项目后，才准备迁移计划。

历史对话可以保留原线程 ID 重新归类，也可以在目标项目创建接续任务。重新归类采用离线、带备份和逐项校验的本地状态更新，不修改对话正文、SQLite 或工作目录。默认保留原对话；当前没有受支持的永久删除接口。该 Skill 目前仅支持并验证 Windows 10、PowerShell 7 和本地 Codex Desktop。

### 三段开发工作流

三段开发工作流包含 `requirement-intake`、`solution-design` 和 `solution-review`，用于把不完整的软件需求逐步整理成可执行交付计划。

推荐顺序是先用 `requirement-intake` 澄清需求，再用 `solution-design` 生成工程方案，最后用 `solution-review` 审查风险并固化最终实施计划。

### 文档编写工作流

文档编写工作流包含 `doc-source-analysis`、`doc-template-outline`、`doc-drafting`、`doc-format-check` 和 `doc-content-proofread`，用于从资料解读、模板适配、正文起草到格式检查和内容校对完成软件项目文档。

推荐顺序是资料解读、模板适配与大纲、正文编写、格式检查、内容校对。

## How To Use These Skills

如果你想使用仓库里的某个 skill，可以只复制对应的 skill 子目录，不需要复制整个仓库。

以 `codex-status-check` 为例，先克隆或下载本仓库，然后在仓库根目录执行：

```powershell
$source = ".\skills\codex-status-check"
$target = Join-Path $env:CODEX_HOME "skills\codex-status-check"
Copy-Item -Recurse -Force $source $target
```

如果没有设置 `CODEX_HOME`，通常可以把 skill 复制到：

```text
~/.codex/skills/codex-status-check
```

安装完成后，在 Codex 中直接调用：

```text
$codex-status-check
```

也可以用自然语言触发：

```text
查看 Codex 当前版本和可升级版本的更新内容
```

具体功能、数据来源和输出格式请查看对应 skill 目录下的 README：

```text
skills/codex-status-check/README.md
```
