# 文档编写 03 正文编写

`doc-drafting` 用于基于大纲、资料解读结果和用户补充信息，起草软件项目文档正文。

## Usage

在 Codex 中直接调用：

```text
$doc-drafting
```

常见用法：

```text
使用 $doc-drafting，基于大纲和资料解读结果起草这一章正文。
```

## Output

输出通常包括：

- 可编辑正文草稿
- 与资料来源对应的事实表达
- 缺失信息标记
- 需要用户确认的假设
- 后续格式检查或内容校对的输入

## Repository Layout

```text
doc-drafting/
  README.md
  SKILL.md
  agents/
    openai.yaml
```
