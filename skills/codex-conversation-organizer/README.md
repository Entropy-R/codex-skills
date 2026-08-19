# Codex 对话迁移与项目整理

`codex-conversation-organizer` 是一个按用户自然语言规则盘点、分类并整理 Codex 对话项目归属的个人 Skill。

它适合处理“把旧项目中的对话按版本、主题、客户或用途迁移到不同项目”这类批量整理任务。分类规则由用户在每次运行时提供，Skill 不内置代码、Git 或业务领域分类表。

## 使用方式

在 Codex 中直接调用：

```text
$codex-conversation-organizer
```

也可以使用中文自然语言触发：

```text
使用“Codex 对话迁移与项目整理”，扫描指定项目中的对话，按照我描述的规则生成分类预览，先不要直接迁移。
```

Skill 会先生成包含任务标题、线程 ID、当前项目、建议项目、证据和不确定性的预览。只有用户确认具体线程到项目的操作清单后，才会准备可执行计划。

## 工作模式

- **盘点**：只读列出源项目中的顶层 Codex 对话。
- **分类计划**：按照用户自然语言规则分类，冲突和证据不足项保持原位等待确认。
- **重新归类**：保留原线程 ID 和完整历史，只改变侧边栏项目归属，不改变原工作目录。
- **创建接续任务**：在目标项目创建新任务并附带精简交接信息，适合后续工作必须运行在目标目录的情况。
- **验证**：逐条核对已批准计划与当前项目归属。

## 迁移后的原对话

- 默认保留原对话。
- 重新归类移动的是原线程本身，不会创建需要删除的副本。
- 创建接续任务后，可以在验证成功后选择保留或归档源任务。
- 当前 Codex 工具没有受支持的永久删除接口；Skill 不会通过删除 SQLite 记录、rollout 文件或会话目录来模拟删除。

## 离线重新归类

任意项目之间的原线程重新归类依赖 Codex Desktop 的本地项目映射，因此采用保守的离线流程：

1. 在 Codex 中盘点、分类并确认具体迁移清单。
2. 生成已批准计划并运行 `WhatIf`。
3. 完全关闭 Codex Desktop。
4. 在外部 PowerShell 7 中运行 Skill 生成的应用命令。
5. 重新打开 Codex，运行验证模式。

应用脚本会检查计划批准状态、线程当前归属、目标项目、旧版未映射线程是否真实存在以及 Codex 是否已退出。写入前创建时间戳备份，并使用原子替换更新项目映射。

它不会修改：

- `state_5.sqlite`
- 对话正文和 rollout
- 附件和生成文件
- 线程工作目录
- Git 仓库或终端进程

## Token 优化

本地盘点和校验脚本不调用模型。实际 Token 消耗主要来自读取对话正文，因此 Skill 默认采用渐进式证据策略：

- 先按项目、归档状态、时间范围和数量限制缩小候选集。
- 首轮只读取标题、项目、时间等紧凑元数据，默认不导出正文预览。
- 只对无法从元数据判断的对话读取少量最近轮次。
- 大批量任务分批处理并保存紧凑分类台账，避免重复读取。
- 范围很大时先做小样本分类，以便在全量分析前修正规则。

## 脚本

```text
scripts/
  collect-conversation-inventory.ps1
  validate-migration-plan.ps1
  apply-assignment-plan.ps1
  verify-assignment-plan.ps1
  tests/
```

- `collect-conversation-inventory.ps1`：只读导出本地顶层对话元数据。
- `validate-migration-plan.ps1`：校验批准状态、线程、项目和当前归属。
- `apply-assignment-plan.ps1`：Codex 退出后原子应用已批准计划并创建备份。
- `verify-assignment-plan.ps1`：只读验证迁移结果。

## 平台与依赖

- 支持平台：Windows 10。
- 已验证：PowerShell 7、本地 Codex Desktop、`sqlite3`。
- macOS 尚未验证，不应运行离线项目归属写入脚本。
- Codex Desktop 内部状态格式可能变化；结构未知或校验失败时，Skill 会停止而不是猜测性写入。

## 验证

```powershell
$skill = Join-Path $env:CODEX_HOME 'skills\codex-conversation-organizer'
pwsh -NoProfile -File (Join-Path $skill 'scripts\tests\run-tests.ps1')
```

fixture 测试覆盖 `WhatIf`、原子备份、显式项目任务、无项目任务、旧版未映射任务、过期计划、未授权计划、重复线程和不存在的目标项目。
