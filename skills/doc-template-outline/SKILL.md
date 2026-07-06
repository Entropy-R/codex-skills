---
name: doc-template-outline
description: Adapt a customer document template and generate an outline using the source-analysis result from a technical agreement. Use when Codex receives a customer template plus the output of doc-source-analysis and needs to produce a document directory, chapter outline, section writing guidance, missing section suggestions, or template-fit plan for software design documents, requirement specifications, test reports, or user manuals.
---

# Document Template Outline

## Goal

Convert the customer template and the first-step source-analysis result into a usable writing skeleton while preserving customer-required structure, terminology, numbering, and acceptance-oriented sections.

## Inputs

Required inputs:

- Customer template, historical template, required table of contents, or customer format file
- Source-analysis result from `$doc-source-analysis`

Optional inputs:

- Target document type: software design document, requirement specification, test report, user manual, or other project document
- Customer formatting rules or historical accepted documents

## Workflow

1. Identify fixed template elements: cover, revision history, approval table, table of contents, required headings, appendix, signature, and formatting constraints.
2. Preserve mandatory customer sections and numbering. Do not rename contractual section titles unless clearly improving only a draft copy.
3. Use the `$doc-source-analysis` result to map each section to writing purpose, required inputs, likely evidence, and missing information.
4. Detect missing but commonly expected software-document sections.
5. Suggest additions only as "建议新增" and explain why they help delivery, acceptance, maintenance, or audit.
6. When the template conflicts with the technical-agreement analysis result, keep the template intact and mark the conflict as a drafting risk.

## Output

Use concise Chinese and prefer:

```markdown
## 文档目录
1. ...

## 章节说明
| 章节 | 写作目标 | 所需输入 | 对应资料解读项 | 注意事项 |

## 模板适配说明
| 模板项 | 处理方式 | 原因 |

## 缺失章节建议
| 建议章节 | 适用原因 | 是否必须 |

## 后续写作输入清单
| 输入 | 用途 | 缺失影响 |
```

## Quality Rules

- Treat the customer template as a format constraint and the source-analysis result as content evidence.
- Keep outline granularity suitable for writing, usually 2 to 3 heading levels.
- Avoid marketing-style sections unless the target document explicitly needs them.
- For test reports, include test scope, environment, cases, execution result, defect summary, conclusion, and residual risk when applicable.
- For user manuals, include target users, installation/login, common workflows, exception handling, FAQ, and support information when applicable.
