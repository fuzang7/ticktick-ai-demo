# Nanobot 使用指南：创建带时间的任务

## 概述

本指南说明如何使用 MCP 服务器的 `add_task` 工具创建带有明确时间（非全天）的任务。

## 工具参数

`add_task` 工具支持以下参数：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 任务标题 |
| `content` | string | 否 | 任务描述/内容 |
| `project_id` | string | 否 | 项目 ID，不提供则使用收件箱 |
| `due_date` | string | 否 | 截止日期，ISO 8601 格式 |
| `startDate` | string | 否 | 任务开始时间，ISO 8601 格式 |
| `timeZone` | string | 否 | 时区，默认为 "Asia/Shanghai" |
| `isAllDay` | boolean | 否 | 是否为全天任务，默认为 true |

## ISO 8601 时间格式

### 推荐格式（含毫秒）
```
YYYY-MM-DDTHH:MM:SS.sss+HHMM
```

例如：
- `2026-02-25T14:00:00.000+0800` - 2026年2月25日下午2点（北京时间）

### 备用格式（无毫秒）
```
YYYY-MM-DDTHH:MM:SS+HH:MM
```

## 使用示例

### 1. 创建带明确时间的任务（非全天）

```json
{
  "name": "add_task",
  "arguments": {
    "title": "团队会议",
    "content": "讨论项目进度",
    "startDate": "2026-02-25T14:00:00.000+0800",
    "timeZone": "Asia/Shanghai",
    "isAllDay": false
  }
}
```

### 2. 创建全天任务

```json
{
  "name": "add_task",
  "arguments": {
    "title": "提交周报",
    "startDate": "2026-02-28T09:00:00.000+0800",
    "isAllDay": true
  }
}
```

### 3. 创建同时有开始时间和截止时间的任务

```json
{
  "name": "add_task",
  "arguments": {
    "title": "线上研讨会",
    "content": "参加AI技术分享",
    "startDate": "2026-02-26T19:00:00.000+0800",
    "due_date": "2026-02-26T21:00:00.000+0800",
    "timeZone": "Asia/Shanghai",
    "isAllDay": false
  }
}
```

## 时间格式注意事项

1. **时区必须正确**：TickTick API 会将时间转换为 UTC 存储
   - 输入：`2026-02-25T14:00:00.000+0800`（北京时间）
   - 存储：`2026-02-25T06:00:00.000+0000`（UTC）

2. **毫秒是可选的但推荐使用**：带毫秒的格式更稳定

3. **isAllDay 默认为 true**：如果不指定 `isAllDay`，任务将创建为全天任务

## 常见问题

### Q: startDate 设置了但不生效？
A: 确保使用正确的 ISO 8601 格式，推荐使用带毫秒的格式：`2026-02-25T14:00:00.000+0800`

### Q: 时间显示不正确？
A: 检查 `timeZone` 参数，确保与 `startDate` 的时区一致

### Q: 如何只设置开始时间不设置截止时间？
A: 只提供 `startDate` 参数，不提供 `due_date` 参数
