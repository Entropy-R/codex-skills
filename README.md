# Codex Skills

这是我的个人 Codex skill 仓库，用来收集和自开发一些好用的 Codex skills。

每个 skill 都放在独立目录中，包含自己的 `SKILL.md`、脚本、配置和说明文档，方便按需安装、迁移和继续扩展。

当前仓库先收录了 `codex-status-check`：它用于查看当前机器的 Codex 版本，并结合 OpenAI Codex changelog、GitHub releases 和 GitHub compare patch，说明从当前版本升级到新版本后实际发生了什么变化。

## Repository Layout

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

新增 skill 时，继续放到：

```text
skills/<skill-name>/
```

每个 skill 目录建议至少包含：

- `SKILL.md`：Codex skill 定义和触发说明。
- `README.md`：面向使用者的安装、调用和功能说明。
- `scripts/`：skill 需要调用的辅助脚本。
- `agents/`：可选的 Codex UI 展示配置。

## Included Skills

| Skill | 调用方式 | 用途 |
| --- | --- | --- |
| `codex-status-check` | `$codex-status-check` | 查询当前 Codex 版本、同通道可升级版本、升级差异、官方产品更新和 GitHub 工程发布参考。 |

## Install A Skill

将需要的 skill 复制到 Codex skills 目录：

```powershell
$source = ".\skills\codex-status-check"
$target = Join-Path $env:CODEX_HOME "skills\codex-status-check"
Copy-Item -Recurse -Force $source $target
```

如果没有设置 `CODEX_HOME`，通常可以使用：

```text
~/.codex/skills/codex-status-check
```

## Usage

在 Codex 中直接调用：

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

## Development

添加新 skill 时建议遵循以下约定：

- 每个 skill 独立放在 `skills/<skill-name>/`。
- 内部标识、目录名和脚本名使用稳定英文名称。
- 面向用户的标题、README 和调用说明可以使用中文。
- 不同 skill 之间不要共享临时文件、缓存或本机配置。
- 如果 skill 需要脚本支持，将脚本放在该 skill 自己的 `scripts/` 目录中。
