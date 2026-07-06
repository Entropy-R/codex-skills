# 文档编写 01 资料解读

`doc-source-analysis` 用于分析技术协议、合同附件、投标技术协议或客户技术规范，提炼后续软件项目文档编写所需的事实、术语、范围、约束和风险。

## Usage

在 Codex 中直接调用：

```text
$doc-source-analysis
```

常见用法：

```text
使用 $doc-source-analysis，分析这份技术协议并输出需求要点、术语、风险和待确认问题。
```

## Output

输出通常包括：

- 项目事实和业务背景
- 功能范围与非功能约束
- 关键术语和命名
- 风险、假设和待确认项
- 可交给模板适配与大纲阶段的资料解读结果

## Repository Layout

```text
doc-source-analysis/
  README.md
  SKILL.md
  agents/
    openai.yaml
```
