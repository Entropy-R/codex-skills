# 文档编写 05 内容校对

`doc-content-proofread` 用于把目标软件项目文档与参考资料对照，检查事实、术语、逻辑、边界、需求追踪和验收风险。

## Usage

在 Codex 中直接调用：

```text
$doc-content-proofread
```

常见用法：

```text
使用 $doc-content-proofread，对照参考资料校对这份软件项目文档内容。
```

## Output

输出通常包括：

- 内容问题清单
- 事实与术语不一致项
- 逻辑缺口和边界风险
- 精确替换建议
- 用户确认后的内容校对版本

## Repository Layout

```text
doc-content-proofread/
  README.md
  SKILL.md
  agents/
    openai.yaml
```
