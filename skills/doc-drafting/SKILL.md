---
name: doc-drafting
description: Draft software project documentation from an outline and analyzed source materials. Use when Codex needs to write, rewrite, expand, or supplement chapter content for software design documents, requirement specifications, test reports, user manuals, or similar engineering documents based on an outline, source-analysis result, customer template, or existing draft.
---

# Document Drafting

## Goal

Write editable first-draft content section by section, using the outline as structure and the source analysis as factual grounding.

## Inputs

- Outline or section list, ideally from `$doc-template-outline`
- Requirement points, terminology, constraints, risks, and clarification questions, ideally from `$doc-source-analysis`
- Optional existing draft text to rewrite, expand, or align
- Target audience and document type if provided

## Workflow

1. Confirm the target section, audience, and writing style from the template or user request.
2. Use the outline to control structure. Do not create new major sections unless the user asks or the outline has an obvious gap.
3. Use source-backed facts directly. Use "待确认" wording for uncertain content instead of silently inventing details.
4. Write in formal engineering Chinese by default: clear, specific, acceptance-oriented, and easy to edit.
5. Keep terminology consistent with the terminology table. Prefer the customer-approved term when available.
6. For missing details, insert short placeholders such as `[待补充：部署服务器规格]` only when necessary.
7. When rewriting, preserve the original intent and improve clarity, consistency, and completeness.

## Output

For full chapters:

```markdown
## 章节标题
正文...

### 小节标题
正文...

> 待确认：...
```

For partial drafting or rewriting, return:

```markdown
## 可替换正文
...

## 使用说明
- 适用章节：...
- 依赖前提：...
- 待补充信息：...
```

## Document-Type Guidance

- Requirement specification: emphasize requirement numbering, actor, trigger, input/output, business rule, exception, and acceptance criteria.
- Software design document: emphasize architecture, modules, interfaces, data flow, deployment, security, error handling, and maintainability.
- Test report: emphasize test basis, scope, environment, execution record, defect statistics, conclusion, and residual risk.
- User manual: emphasize task flow, UI operation steps, expected result, common exceptions, and support path.

## Quality Rules

- Do not over-polish into sales copy.
- Avoid vague claims like "系统稳定可靠" unless backed by measurable requirements or test results.
- Keep paragraphs short enough for direct editing in Word.
- Add concise Chinese comments only for unresolved assumptions or business rules that may affect acceptance.
- When the user asks to generate an editable document file, choose the output location by priority:
  1. Use the explicit output path given by the user.
  2. If drafting from an existing local document or template, place the generated file beside the original file unless the user asks otherwise.
  3. If this skill is invoked from a specific working directory, generate the file in that directory.
  4. Use the current project's designated document-writing workflow directory only when uploaded materials need to be collected there or no more specific local output location is available.
