---
name: doc-content-proofread
description: Proofread software project document content against user-provided references. Use when Codex needs to check requirement specifications, design documents, test reports, user manuals, or similar documents for factual consistency, terminology consistency, logical completeness, boundary conditions, requirement traceability, acceptance risk, source conflicts, and precise replacement suggestions after document formatting has been handled separately.
---

# Document Content Proofread

## Goal

Review an already written document against a user-provided reference document, then produce a content-corrected `.docx` document only after the user confirms the proposed changes. When the target document conflicts with the reference document, treat the user-provided reference document as the authority.

This skill handles content quality only. Do not spend effort normalizing layout, heading style, table style, page numbers, or other formatting issues; route those to `$doc-format-check`.

Output location priority: use the explicit output path given by the user; otherwise place generated documents beside the original local target document or reference document; otherwise use the current working directory where this skill is invoked. Use the current project's designated document-writing workflow directory only when uploaded materials need to be collected there or no more specific local output location is available.

## Inputs

Required input:

- Target document to review and modify
- User-provided reference document used as the baseline for conflict resolution

Recommended supporting inputs:

- Technical agreement or `$doc-source-analysis` result
- Customer template or `$doc-template-outline` result, for structure expectations only
- Terminology table, customer rules, review focus, or known risk list
- Format-normalized draft from `$doc-format-check`, if available

## Workflow

1. Identify document type, review scope, expected `.docx` output name, and whether the document has already passed format check.
2. Compare the target document with the user-provided reference document. When the two conflict, mark the target document content as needing correction and use the reference document as the basis.
3. Check factual consistency against the technical agreement or source-analysis result when provided. If these sources conflict with the user-provided reference document, pause and list the conflict for user confirmation instead of choosing silently.
4. Check terminology, abbreviations, naming, numbering used as business identifiers, units, interface names, module names, role names, and status names.
5. Check logical completeness: scope, prerequisites, workflow, exception handling, boundary conditions, input/output, acceptance criteria, dependencies, residual risk, and traceability.
6. Check document-type content risks:
   - Requirements: missing actor, trigger, input, output, rule, exception, priority, or acceptance condition
   - Design: missing module responsibility, data flow, interface contract, error handling, deployment constraint, or security control
   - Test report: missing test scope, environment, case execution basis, defect conclusion, or residual issue
   - User manual: missing operation precondition, step result, exception handling, or role permission note
7. First provide a content issue list and modification suggestions. Do not edit or generate the revised `.docx` until the user confirms.
8. After confirmation, apply confirmed edits into a reviewed `.docx` document. For unconfirmed or uncertain changes, preserve the original meaning and add a clear review note instead of silently rewriting.
9. Generate a `.docx` output. If direct DOCX editing is not possible in the environment, create a Markdown review draft plus a clear note explaining why DOCX generation was blocked.

## Output

Primary output:

- Before user confirmation: a content issue list and modification suggestions only
- After user confirmation: a reviewed `.docx` document saved according to the output location priority, usually named with `_内容校对版.docx` or `_校对审查版.docx`

Chat summary:

```markdown
## 输出文件
- 文件：...

## 问题清单
| 编号 | 风险等级 | 位置 | 问题 | 处理方式 |

## 主要修改
| 位置 | 修改说明 | 原因 |

## 依据冲突
| 位置 | 冲突来源 | 需确认事项 |

## 遗留风险
| 风险 | 原因 | 建议 |
```

## Risk Levels

- 高：可能导致验收失败、合同争议、严重误导、关键功能缺失或测试结论不可信。
- 中：影响理解、维护、测试复现、跨章节一致性或客户评审效率。
- 低：局部措辞、轻微冗余、非关键描述不清或不影响结论的小问题。

## Quality Rules

- Use the user-provided reference document as the baseline when it conflicts with the target document.
- Do not modify the target document or generate the reviewed `.docx` before the user confirms the modification list.
- Produce a `.docx` file as the final artifact whenever tooling allows it.
- Choose the output location by priority: explicit user path, original target/reference file directory, current working directory, then the current project's designated document-writing workflow directory only for uploaded-material collection or when no more specific local output location is available.
- Lead the chat response with the output file and high-risk issues.
- Do not rewrite the whole document unless asked.
- Distinguish source conflict from writing quality issue.
- If a problem depends on missing source evidence, mark it as "需依据确认".
- Do not perform broad formatting cleanup in this skill; recommend `$doc-format-check` for format issues.
- Prefer precise edits in the document over generic advice in chat.
