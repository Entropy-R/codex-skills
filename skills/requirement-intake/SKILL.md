---
name: requirement-intake
description: Use when Codex needs to turn an incomplete or unstructured product/software request into a structured requirement intake, actively ask clarifying questions, identify missing or ambiguous information, and prepare a stable input package for a later solution-design stage. Triggers include Chinese requests like “01 需求理解与澄清”, “需求理解与澄清”, “帮我澄清需求”, “第一阶段”, “需求还不完整”, “先问我问题”, or requests involving text, image-dialog descriptions, document excerpts, or vague feature ideas.
---

# 01 需求理解与澄清

## 工作目标

先理解原始需求，再主动澄清。不要直接输出完整实现方案；本阶段产物必须能作为“实现方案设计”阶段的输入。

## 输入

要求用户或上文提供：

```text
原始需求：
【文字需求、图片对话描述或文档摘录】

输入类型：
【文字 / 图片对话 / 文档 / 其他】

已知背景：
【项目背景、业务背景、用户群体、现有系统情况；没有就写“暂无”】

期望输出：
【默认：成熟工程实现方案】
```

如果用户没有按模板提供，也要从上下文中尽量提取，并说明缺失项。

## 处理规则

1. 先输出结构化需求理解。
2. 主动识别缺失、含糊、冲突或可能被误解的信息。
3. 把疑惑转成明确问题询问用户，区分“必须回答”和“建议回答”。
4. 对每个问题说明为什么要问，以及会影响后续方案的哪个部分。
5. 可以给默认假设，但不能用默认假设掩盖高风险未知项。
6. 如果关键信息缺失，明确说明暂不建议进入下一阶段。

## 输出格式

### 需求理解摘要

- 原始需求想解决的问题：
- 目标用户或使用者：
- 主要使用场景：
- 期望结果：

### 确认后的目标

- 核心目标：
- 次要目标：
- 不确定目标：

### 范围与非范围

- 当前应包含：
- 当前不应包含：
- 需要进一步确认：

### 约束与风险

- 业务约束：
- 技术约束：
- 时间或资源约束：
- 主要风险：

### 关键澄清问题

| 优先级 | 问题 | 为什么要问 | 影响范围 | 默认假设 |
| --- | --- | --- | --- | --- |
| 必须回答 |  |  |  |  |
| 建议回答 |  |  |  |  |

### 我的疑惑

- 我目前不确定的是：
- 这些疑惑如果不确认，可能导致：

### 进入下一阶段前必须回答

-

### 默认假设

- 如果用户不补充信息，将默认：

### 是否建议进入下一阶段

结论：【建议进入 / 暂不建议进入】

原因：

下一步建议：

### 给实现方案设计阶段的输入包

- 本阶段需求理解摘要：
- 已确认信息：
- 用户仍需补充的问题：
- 默认假设：
- 不建议进入下一阶段时的阻塞原因：
