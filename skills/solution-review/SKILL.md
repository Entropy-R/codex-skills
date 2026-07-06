---
name: solution-review
description: Use when Codex needs to review an engineering implementation plan, identify omissions, conflicts, ambiguity, feasibility risks, and then rewrite it into a final executable delivery plan. Triggers include Chinese requests like “03 方案审查与落地化”, “方案审查与落地化”, “第三阶段”, “审查这个方案”, “输出最终成熟实现方案”, or requests for acceptance criteria, test suggestions, task priorities, risks, and pre-implementation confirmations.
---

# 03 方案审查与落地化

## 工作目标

先审查第二阶段实现方案，再整合为最终可执行的成熟工程方案。不要跳过评审直接重写。

## 输入

```text
第二阶段方案：
【粘贴实现方案设计阶段的完整输出】

评审关注点：
【默认：全面评审】

最终输出偏好：
【默认：适合交给开发执行】
```

如果缺少第二阶段方案，要先要求用户补充；只有上下文中已有等价方案时，才继续评审。

## 处理规则

1. 先审查完整性、一致性、可实施性、风险和验收口径。
2. 指出方案中的遗漏、冲突、含糊点和实现风险。
3. 将审查结论整合成最终成熟实现方案。
4. 最终方案偏工程落地，避免泛泛 PRD。
5. 如果仍存在高风险未知项，标为“实施前必须确认”。

## 输出格式

### 评审结论

- 完整性：
- 一致性：
- 可实施性：
- 主要问题：

### 需要修正或补充的内容

| 问题 | 影响 | 修正建议 |
| --- | --- | --- |
|  |  |  |

### 最终成熟实现方案

#### 方案摘要

-

#### 实现范围

-

#### 模块设计

| 模块 | 职责 | 输入 | 输出 |
| --- | --- | --- | --- |
|  |  |  |  |

#### 流程与接口

- 核心流程：
- 输入接口：
- 输出接口：
- 异常处理：

#### 任务拆分

| 优先级 | 任务 | 交付物 | 验收标准 |
| --- | --- | --- | --- |
| P0 |  |  |  |
| P1 |  |  |  |
| P2 |  |  |  |

#### 验收标准

-

#### 测试建议

-

#### 风险与待确认事项

- 实施前必须确认：
- 可接受风险：
- 后续优化：
