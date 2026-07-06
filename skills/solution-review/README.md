# 三段开发 03 方案审查与落地化

`solution-review` 用于审查工程实现方案，发现遗漏、冲突、歧义和可行性风险，并整理最终可执行交付计划。

## Usage

在 Codex 中直接调用：

```text
$solution-review
```

常见用法：

```text
使用 $solution-review，审查这份方案并输出最终可执行工程方案。
```

## Output

输出通常包括：

- 方案问题和风险清单
- 待确认事项
- 修订后的最终实施计划
- 验收标准和测试建议
- 优先级与落地顺序

## Repository Layout

```text
solution-review/
  README.md
  SKILL.md
  agents/
    openai.yaml
```
