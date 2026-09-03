# 前端页面开发

`frontend-page-development` 用于在现有 TypeScript + React 前端工程中，从 0 到 1 设计并实现业务页面或管理后台页面，尤其适用于 Umi Max 项目。

它会先检查页面、路由、UI 组件、请求和样式等现有基础设施，澄清页面目标与接口契约，再输出最小可行方案；页面实现采用静态 UI 优先、视觉确认后接入真实 API 的节奏。

## Usage

在 Codex 中直接调用：

```text
$frontend-page-development
```

常见用法：

```text
使用 $frontend-page-development，为现有 Umi Max 项目开发订单详情页面。
```

也可以直接描述需要开发的 React、Umi Max、业务后台或管理后台页面，由 Codex 自动匹配此 Skill。

## Output

输出通常包括：

- 基于项目现状的最小可行页面方案
- 页面区域、组件、状态、交互、路由和 API 说明
- 静态 UI、视觉调整、交互和接口接入的实施顺序
- 按验收条件完成的验证结果与遗留风险

## Repository Layout

```text
frontend-page-development/
  README.md
  SKILL.md
  agents/
    openai.yaml
```
