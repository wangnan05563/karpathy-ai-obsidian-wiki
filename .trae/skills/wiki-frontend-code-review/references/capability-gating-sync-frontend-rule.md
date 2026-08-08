# 能力门控同步（FR-076）

> 复盘来源：归档门控漂移——后端已将"是否可归档"的判断从依赖 `sessionId` 存在改为从请求体取内容可得性解耦，但前端 `:can-archive` 仍依赖 `!!sessionId` 等过期契约，导致后端放宽后前端功能卡死。本规则要求前端能力门控须与后端契约同步放宽、在同一变更内完成。对应 wiki-code-dev capability-gating-sync-rule.md（CODING-CAPABILITY-GATING-SYNC）。
> 所有可变参数从 [config/review-config.md](../config/review-config.md) 的"capability_gating_sync"章节读取，禁止在本规则文件硬编码门控模式。

## Trigger Keywords
!!sessionId, !!getSession, v-if, :can-archive, canArchive, 门控, 能力门控, 内容可得性, content availability, 放宽, 解耦

## Rules

### FR-076-1: 前端能力门控须与后端契约同步放宽

- **Severity**: critical
- **Description**: 当后端放宽某能力判定（如归档从"依赖会话存在"改为"内容可得即可"）时，前端对应的能力门控（如 `:can-archive` 依赖 `!!sessionId`）必须同步放宽，否则功能卡死。`capability_gating_sync.stale_gating_patterns`（默认 `!!sessionId,!!getSession`）命中即告警；`capability_gating_sync.relax_signal` 默认 `content availability` —— 前端门控应基于"内容可得性"而非"会话存在"。
- **Suggested fix**:
```typescript
// 错误：前端门控仍依赖过期契约（后端已改为内容可得性）
const canArchive = !!sessionId
// 正确：与后端契约同步，基于内容可得性
const canArchive = props.contentAvailable ?? !!sessionId
// 且后端放宽须在同一次变更内完成前端同步
```

### FR-076-2: 前后端门控放宽须同一变更完成

- **Severity**: critical
- **Description**: `capability_gating_sync.complete_in_same_change` 默认 true —— 后端契约放宽与前端门控同步必须在**同一变更**内完成，禁止"后端先放宽、前端后续 PR 才跟上"的割裂，否则中间态功能卡死或前后端口径不一致。

## 关键参数（从 config 读取）

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `capability_gating_sync.enabled` | `true` | 是否启用本规则 |
| `capability_gating_sync.sync_with_backend_contract` | `true` | 前端门控须与后端契约同步放宽 |
| `capability_gating_sync.relax_signal` | `content availability` | 放宽依据（内容可得性而非 sessionId 存在） |
| `capability_gating_sync.stale_gating_patterns` | `!!sessionId,!!getSession` | 过期门控依赖模式（命中即告警） |
| `capability_gating_sync.complete_in_same_change` | `true` | 前后端放宽须同一变更完成 |
| `capability_gating_sync.severity` | `critical` | 门控漂移导致功能卡死违规级别 |

## 检查方式

1. Grep 检索 `capability_gating_sync.stale_gating_patterns`（如 `!!sessionId` / `!!getSession`）在门控表达式中的使用。
2. 若后端已放宽但前端门控仍命中过期模式 → FR-076-1 违规。
3. 若后端契约变更与前端门控同步不在同一变更 → FR-076-2 违规。

## 适配新项目

- **无后端契约耦合的纯前端开关**：本规则不适用（门控本就前端自决）。
- **不同门控模式**：调整 `stale_gating_patterns` 匹配本项目过期契约特征。
