---
name: doc-format-check
description: Check and normalize software project document formatting against a fixed template. Use when Codex needs to inspect or revise DOCX/Markdown software documents for optional cover page consistency, revision history, table of contents, heading levels, fonts, numbering, table style, figure/table captions, optional appendix/attachment format, page header/footer, page numbers, and structure/template compliance before content proofreading.
---

# Document Format Check

## Goal

Check a software project document against a fixed formatting template, then produce a format-normalized `.docx` document only after the user confirms the proposed changes. This skill handles document structure and presentation only; do not judge whether the business or technical content is factually correct.

By default, use `assets/software-doc-format-template.md` as the baseline template. If the user provides a customer template, compare it with the baseline first and ask whether the customer template should override the baseline for that task.

Output location priority: use the explicit output path given by the user; otherwise place generated documents beside the original local target document or template; otherwise use the current working directory where this skill is invoked. Use the current project's designated document-writing workflow directory only when uploaded materials need to be collected there or no more specific local output location is available.

## Inputs

Required input:

- Target document to check and normalize

Optional input:

- Customer-provided document template
- Expected document type, such as requirement specification, software design document, test report, or user manual
- Existing outline from `$doc-template-outline`
- Customer formatting rules

## Workflow

1. Identify document type, target document path, expected output name, and whether a customer template is provided.
2. Load the fixed baseline template from `assets/software-doc-format-template.md`.
3. If a customer template is provided, compare it with the baseline template and list conflicts. Ask the user whether to use the customer template, the baseline template, or a merged rule set before modifying the document.
4. Check structure and format only:
   - Cover page fields and order when a cover page exists, or cover page suggestions when the document has no cover
   - Revision history table
   - Table of contents placement
   - Heading levels and numbering
   - Font, size, bold, alignment, and spacing consistency for headings, body text, captions, tables, figures, headers, and footers
   - Paragraph spacing, indentation, alignment, and list style
   - Table style, column headers, notes, and numbering
   - Figure/table caption format, required in-text cross-references, and caption number consistency
   - Terminology/abbreviation section placement
   - Header/footer, page number, and optional appendix/attachment format when present
   - Required section presence for the selected document type
5. Do not rewrite factual claims, requirements, interface definitions, test conclusions, or acceptance criteria. If content appears suspicious or an intended edit depends on missing information, ask the user to confirm before writing instead of inventing content. Mark content issues as "转内容校对确认" when appropriate.
6. First provide a format modification plan, format issue list, and proposed changes. Do not edit the target document or generate the revised `.docx` until the user confirms the plan.
7. After confirmation, apply only the confirmed formatting changes into a `.docx` document. Preserve original wording unless a minimal heading/table label adjustment is necessary for template compliance.
8. If direct DOCX editing is not possible, create a Markdown format-normalized draft plus a clear note explaining why DOCX generation was blocked.

## Output

Primary output:

- Before user confirmation: format issue list and modification suggestions only
- After user confirmation: a format-normalized `.docx` document saved according to the output location priority, usually named with `_格式检查版.docx`

Chat summary:

```markdown
## 输出文件
- 文件：...

## 格式问题清单
| 编号 | 风险等级 | 位置 | 问题 | 处理方式 |

## 主要格式修改
| 位置 | 修改说明 | 模板依据 |

## 转内容校对确认
| 位置 | 原因 | 建议 |

## 遗留风险
| 风险 | 原因 | 建议 |
```

## Risk Levels

- 高：模板关键结构缺失、章节顺序严重错误、编号体系混乱、目录/页码不可用，可能影响客户验收或正式归档。
- 中：标题层级、表格、图表编号、术语章节、附件格式不一致，影响评审效率和文档可维护性。
- 低：局部间距、标点、字体、轻微样式不一致，不影响阅读结论。

## Quality Rules

- Use `assets/software-doc-format-template.md` as the default formatting authority.
- Prefer a user-provided customer template when the user explicitly confirms it should override the baseline.
- Do not perform content proofreading in this skill.
- Do not modify the target document or generate the reviewed `.docx` before the user confirms the format modification plan and change list.
- Produce a `.docx` file as the final artifact whenever tooling allows it.
- Choose the output location by priority: explicit user path, original target/template file directory, current working directory, then the current project's designated document-writing workflow directory only for uploaded-material collection or when no more specific local output location is available.
- Preserve original wording except for minimal format labels, heading numbering, captions, and table headers required by the template.
- Do not fill uncertain content by assumption. Ask the user for confirmation before writing any uncertain text, screenshot description, path, term, enum value, or caption.
- Mark suspected content problems as "转内容校对确认" and recommend `$doc-content-proofread`.
