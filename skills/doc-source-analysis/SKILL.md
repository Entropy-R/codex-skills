---
name: doc-source-analysis
description: Analyze a technical agreement for software project documentation. Use when Codex receives a technical agreement, contract attachment, tender technical protocol, or customer technical specification and needs to extract facts, terminology, scope, constraints, risks, assumptions, and clarification questions before drafting software design documents, requirement specifications, test reports, or user manuals. Additional materials may be used only as supplements when the agreement is too large, incomplete, or ambiguous.
---

# Document Source Analysis

## Goal

Turn the technical agreement into a reliable evidence base for later writing. Treat the technical agreement as the primary source, and use extra materials only as supplemental evidence when the user provides them.

## Inputs

Primary input:

- Technical agreement, contract attachment, tender technical protocol, or customer technical specification

Optional supplemental inputs:

- Customer requirement notes, meeting minutes, existing materials, interface descriptions, or historical documents
- Use supplemental materials only to clarify missing, excessive, ambiguous, or conflicting content in the technical agreement

## Workflow

1. Identify the technical agreement type, project background, customer, and intended downstream document.
2. Extract source-backed facts from the technical agreement: business goals, system boundary, users, functions, interfaces, data, environment, performance, security, delivery, acceptance, and maintenance constraints.
3. Normalize terminology. Record original term, preferred term, aliases, and ambiguity.
4. Separate requirement types: functional, non-functional, interface, data, operation, deployment, compliance, acceptance, and out-of-scope.
5. Mark conflicts, missing information, implicit assumptions, and statements that need customer confirmation.
6. When supplemental materials are provided, mark whether each conclusion comes from the technical agreement or from supplemental evidence.
7. Preserve evidence references when possible: file name, section title, page, paragraph, table, or quoted short phrase.

## Output

Use concise Chinese unless the user requests another language. Prefer this structure:

```markdown
## 需求要点清单
| 编号 | 类型 | 要点 | 依据来源 | 确认状态 |

## 术语表
| 术语 | 含义 | 别名/原文 | 使用建议 |

## 范围与约束
| 项目 | 内容 | 依据来源 | 影响 |

## 风险点
| 风险等级 | 问题 | 依据来源 | 建议 |

## 待澄清问题
| 优先级 | 问题 | 背景 | 建议询问对象 |
```

## Quality Rules

- Do not invent requirements to fill gaps.
- Treat the technical agreement as the authority unless the user explicitly says another source has higher priority.
- Label uncertain conclusions as "推断" or "待确认".
- Keep customer wording for legally or contractually sensitive terms.
- Highlight contradictions before trying to reconcile them.
- If evidence is weak, say so directly and suggest the next document or stakeholder to check.
