# Type Sync Rule

## 触发关键词

interface, type, types.ts, frontend types, backend types, vue-tsc, tsc, 字段对齐, 类型不同步, 全栈类型

## 规则描述

### TS-1：后端与前端共享类型必须字段对齐

**严重级别**：critical

后端 `types.ts`（默认 `api/src/types.ts`）与前端 `types.ts`（默认 `frontend/src/types.ts`）中同名 `interface` / `type` 的字段定义必须完全对齐：字段名、字段类型、可选性（`?`）、字面量联合类型全部一致。

**为什么**：全栈项目通常后端先新增字段，前端 types.ts 同步遗漏。后端返回新字段时前端类型不识别，运行期数据存在但 TypeScript 静态检查通过（因为有 `any` 或宽松类型潜伏），导致前端代码无法引用新字段，或引用后 vue-tsc 报错阻断构建。这类问题在缺少端到端类型校验的项目中反复出现。

## 判断逻辑

```
1. 读取 <backend_types_path> 与 <frontend_types_path>（默认见 config）
2. 提取两份文件中所有 interface / type 名称
3. 对每个同名声明逐字段对比：
   - 字段名缺失 → error（一边有一边无）
   - 字段类型不同 → error（如后端 string，前端 string | null）
   - 可选性不同 → error（如后端必填，前端可选）
   - 字面量联合不同 → error（如后端 'a'|'b'，前端 'a'|'b'|'c'）
4. 仅在后端存在的 interface → 警告（可能是前端未消费，或需要同步）
5. 仅在前端存在的 interface → 警告（可能是后端已删除，或前端独立类型）
6. 通过 vue-tsc / tsc --noEmit 作为门禁：
   - 后端：cd api && npx tsc --noEmit
   - 前端：cd frontend && npx vue-tsc --noEmit
7. 任一报错 → 阻断提交
```

## 适用场景

- 全栈 TypeScript 项目（后端 Node.js + 前端 Vue/React/SPA）
- 前后端通过共享 types.ts 维持契约的项目（无 OpenAPI 自动生成）
- Monorepo 结构（frontend + api 各自维护 types.ts）
- 后端为前端 BFF 层，类型需手工同步的场景

## 不适用场景

- 后端独立运行无前端（如纯 API 服务、CLI 工具）
- 使用 OpenAPI / GraphQL 自动生成前端类型的项目（契约由代码生成保证）
- 前端类型完全由后端单边导出（monorepo 共享 types 包，无同步问题）
- 微服务架构下不同服务的内部类型（不共享）

## 配置参数

> 所有参数从 `config/coding-standards-config.md` 的 `type_sync` 段读取。

| 参数 | 默认值 | 用途 |
|------|--------|------|
| `backend_types_path` | `api/src/types.ts` | 后端类型文件相对路径 |
| `frontend_types_path` | `frontend/src/types.ts` | 前端类型文件相对路径 |
| `backend_typecheck_command` | `npx tsc --noEmit` | 后端类型检查命令 |
| `frontend_typecheck_command` | `npx vue-tsc --noEmit` | 前端类型检查命令（Vue 项目用 vue-tsc） |
| `allow_frontend_extra_fields` | `false` | 是否允许前端类型包含后端没有的字段（如前端展示用扩展字段） |
| `allow_optional_mismatch` | `false` | 是否允许后端必填 / 前端可选的差异 |

## 示例

### 错误示例

后端新增 `TunnelConfig` 接口：

```typescript
// api/src/types.ts
export interface TunnelConfig {
  provider: 'ngrok' | 'cloudflared';
  authToken: string;
  port: number;
  region?: string;  // 新增字段
}
```

前端 types.ts 未同步：

```typescript
// frontend/src/types.ts
export interface TunnelConfig {
  provider: 'ngrok' | 'cloudflared';
  authToken: string;
  port: number;
  // ❌ 缺少 region 字段
  // 后端返回 region 时前端 TS 类型不识别
  // 前端代码引用 config.region 会报 TS2339
}
```

### 正确示例

```typescript
// frontend/src/types.ts
export interface TunnelConfig {
  provider: 'ngrok' | 'cloudflared';
  authToken: string;
  port: number;
  region?: string;  // ✅ 与后端对齐
}
```

### 检测脚本片段

```powershell
# $backendTypes、$frontendTypes、$typecheckCmds 由调用方从 config 读取后传入
function Test-TypeSync {
  param(
    [string]$BackendPath,
    [string]$FrontendPath
  )
  # 简化检测：用正则提取两边的 interface 名称，取交集逐个对比
  $backendContent = Get-Content $BackendPath -Raw
  $frontendContent = Get-Content $FrontendPath -Raw

  $backendInterfaces = [regex]::Matches($backendContent, 'interface\s+(\w+)') | ForEach-Object { $_.Groups[1].Value }
  $frontendInterfaces = [regex]::Matches($frontendContent, 'interface\s+(\w+)') | ForEach-Object { $_.Groups[1].Value }

  $common = Compare-Object $backendInterfaces $frontendInterfaces -IncludeEqual -ExcludeDifferent -PassThru
  foreach ($name in $common) {
    # 进一步提取字段对比（此处简化，实际可用 ts-morph 等工具）
    Write-Host "检查 interface $name 的字段对齐..."
  }

  # 类型检查门禁
  foreach ($cmd in $typecheckCmds) {
    Invoke-Expression $cmd
    if ($LASTEXITCODE -ne 0) {
      Write-Error "类型检查失败：$cmd"
      exit 1
    }
  }
}
```

### 类型检查门禁

```powershell
# 类型检查命令从 config 读取
# 后端
Push-Location api
npx tsc --noEmit
if ($LASTEXITCODE -ne 0) { exit 1 }
Pop-Location

# 前端
Push-Location frontend
npx vue-tsc --noEmit
if ($LASTEXITCODE -ne 0) { exit 1 }
Pop-Location
```

## 检查清单

- [ ] 后端新增 / 修改 interface 时是否同步前端 types.ts
- [ ] 同名 interface 的字段名是否完全一致
- [ ] 同名 interface 的字段类型是否完全一致
- [ ] 同名 interface 的可选性（`?`）是否一致
- [ ] 字面量联合类型是否两端对齐
- [ ] 提交前是否执行后端 tsc --noEmit 门禁
- [ ] 提交前是否执行前端 vue-tsc --noEmit 门禁
- [ ] 删除后端 interface 时是否同步删除前端定义
