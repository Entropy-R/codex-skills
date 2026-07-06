# 文档编写 04 格式检查

`doc-format-check` 用于按固定软件项目文档模板检查并统一文档结构、编号、表格、标题层级和版式。

## Usage

在 Codex 中直接调用：

```text
$doc-format-check
```

常见用法：

```text
使用 $doc-format-check，按模板检查这份软件项目文档的格式。
```

## Output

输出通常包括：

- 格式问题清单
- 建议调整项
- 用户确认后的格式归一化文档
- 无法自动判断的模板差异说明

## Repository Layout

```text
doc-format-check/
  README.md
  SKILL.md
  agents/
    openai.yaml
  assets/
    software-doc-format-template.md
```
