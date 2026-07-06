# 三段开发 01 需求理解与澄清

`requirement-intake` 用于把不完整或非结构化的软件需求整理成稳定的需求输入包，并主动提出必须澄清的问题。

## Usage

在 Codex 中直接调用：

```text
$requirement-intake
```

常见用法：

```text
使用 $requirement-intake，帮我整理这段原始需求并提出必须确认的问题。
```

## Output

输出通常包括：

- 需求目标和用户场景
- 已知信息与缺失信息
- 边界、约束和风险
- 必须向用户确认的问题
- 可交给下一阶段的需求输入包

## Repository Layout

```text
requirement-intake/
  README.md
  SKILL.md
  agents/
    openai.yaml
```
