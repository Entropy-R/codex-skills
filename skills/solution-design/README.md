# 三段开发 02 实现方案设计

`solution-design` 用于基于已确认需求和仓库事实，把中大型软件变更转换成复杂度受控、可验证且可执行的工程实现方案。简单局部修改不需要套用完整流程。

## Usage

在 Codex 中直接调用：

```text
$solution-design
```

常见用法：

```text
使用 $solution-design，基于第一阶段输出和我的补充回答生成工程实现方案。
```

## Output

输出始终包括：

- 方案摘要与明确非范围
- 本次必要的关键设计
- 验证方案
- 假设、风险和阻塞项

只有任务实际涉及时，才补充公共接口、持久化模型、兼容、迁移、安全、并发、恢复或实施顺序；不输出空模板，也不在本阶段拆正式 Ticket。

## Design Principles

本 skill 为本仓库自制内容，概念上参考以下公开资料关于先查证、最小方案、局部变更、可验证目标和失败可见性的工程原则，规则均重新组织和独立表述：

- [Karpathy Guidelines](https://github.com/emavv/karpathy-guidelines)
- [FerroxLabs AGENTS.md](https://github.com/FerroxLabs/agents-md)
- [Avoid Over-Defensive Programming](https://github.com/aravelo7/codex-agent-skills/blob/main/skills/avoid-overdefensive-programming/SKILL.md)

## Repository Layout

```text
solution-design/
  README.md
  SKILL.md
  agents/
    openai.yaml
```
