# Codex Skills

这是一个用于管理多个 Codex skill 的本地聚合仓库。每个 skill 都放在独立目录中，便于后续手动上传到 GitHub、迁移到其它机器，或按需复制到 Codex skills 目录。

## 目录结构

```text
codex-skills/
  skills/
    codex-status-check/
      README.md
      SKILL.md
      agents/
        openai.yaml
      scripts/
        codex_status_check.py
```

后续新增 skill 时，继续使用：

```text
skills/<skill-name>/
```

## 当前 Skills

| Skill | 调用方式 | 用途 |
| --- | --- | --- |
| `codex-status-check` | `$codex-status-check` | 查询当前 Codex 版本、同通道可升级版本、升级差异、官方产品更新和 GitHub 工程发布参考。 |

## 安装单个 Skill

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

## 使用方式

在 Codex 中直接调用：

```text
$codex-status-check
```

也可以用自然语言触发，例如：

```text
查看 Codex 当前版本和可升级版本的更新内容
```

## 隐私与脱敏

这个仓库不应包含以下内容：

- 本机绝对路径，例如用户目录、工作盘路径、应用安装路径。
- Codex 本地配置、SQLite 状态库、运行快照、日志、缓存。
- 账号、令牌、API key、cookie 或其它凭据。
- `__pycache__`、`.pyc`、虚拟环境、构建产物。

仓库中的脚本如需展示本机路径，应使用 `~` 替代用户主目录，避免在公开仓库或 issue 中暴露本机用户名。

## 上传前检查

上传到 GitHub 前建议运行：

```powershell
rg -n "<your-user-name>|<local-workspace-path>|<app-data-path>|<local-executable-path-field>" .
```

如果扫描有命中，确认是否属于说明性占位或需要继续脱敏。
