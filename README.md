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
```

这个仓库采用聚合式结构：仓库根目录只放整体说明和通用配置，所有可用的 Codex skill 都放在 `skills/` 下。每个 skill 都是一个相对独立的单元，可以单独复制、安装和使用。

`skills/<skill-name>/SKILL.md` 是 Codex 识别 skill 的核心文件；`README.md` 用来说明该 skill 的用途和调用方式；`scripts/` 和 `agents/` 则按需存放辅助脚本和展示配置。

## Included Skills

| Skill | 调用方式 | 用途 |
| --- | --- | --- |
| `codex-status-check` | `$codex-status-check` | 查询当前 Codex 版本、同通道可升级版本、升级差异、官方产品更新和 GitHub 工程发布参考。 |

### codex-status-check

`codex-status-check` 用于查看当前机器上的 Codex 版本，并结合 OpenAI Codex changelog、GitHub releases 和 GitHub compare patch，说明从当前版本升级到新版本后实际发生了什么变化。

它会区分“与当前 CLI 版本相关的同通道更新”和“仅供参考的其它工程发布”，避免把 alpha/stable 等不同通道的更新混在一起。对于 release note 过于简略的版本，它会尝试读取 GitHub compare patch，补充 commit 摘要、影响说明和涉及文件范围。

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
