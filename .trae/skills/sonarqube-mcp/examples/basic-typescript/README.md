# Basic TypeScript - 最小 TypeScript 项目配置示例

> **适用场景**：纯 TypeScript 项目（Node.js CLI、库、工具），无 React/Vue 等前端框架。

## 包含内容

```
basic-typescript/
├── config/
│   └── project_config.json       # 最小 TypeScript 项目配置
└── README.md                      # 本文件
```

## 配置特点

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 后端语言 | TypeScript | 仅支持 TypeScript |
| 启用的框架 | 无 | 不加载任何框架模式 |
| 后端路径 | `src` | 标准 TypeScript 项目结构 |
| 测试命令 | `npm test` | 仅后端测试 |
| 报告目录 | `docs/sonar-reports/` | 项目内归档 |
| 业务约束 | 空 | 仅加载 `core.json` 通用规则 |

## 启用的硬约束

- **core.json**（通用安全规则）
- **不启用任何业务规则**（`business_constraints.load_files: []`）

## 使用方法

### 1. 复制到项目

```powershell
Copy-Item -Path "examples/basic-typescript/config/project_config.json" -Destination ".trae/skills/sonarqube-mcp/config/project_config.json" -Force
```

### 2. 修改项目信息

```json
{
  "project": {
    "key": "my_typescript_project",
    "name": "My TypeScript Project",
    "base_path": "."
  },
  "modules": {
    "backend": {
      "path": "src",
      "languages": ["typescript"],
      "frameworks": [],
      "layers": {
        "core": "core",
        "utils": "utils",
        "types": "types"
      },
      "exclude": ["node_modules", "dist", "build", ".git", "coverage", "*.test.ts", "*.spec.ts"]
    }
  }
}
```

### 3. 设置环境变量

> 具体值由用户根据自身环境填入，禁止硬编码。完整变量清单见 SKILL.md "配置环境变量" 章节。

```powershell
$env:SONAR_TOKEN = "<your-sonar-token>"
$env:SONARQUBE_URL = "<your-server-host>"
$env:SONARQUBE_PORT = "<your-server-port>"
$env:SONAR_PROJECT_KEY = "<your-project-key>"
```

### 4. 验证并扫描

```powershell
.\scripts\verify-connection.ps1
.\scripts\run-sonar-scanner.ps1
```

## 预期输出

- 加载 v2.3 配置（core+project）
- 仅加载通用核心安全规则
- 不进行任何框架误报识别
- 不加载任何业务约束

## 适用项目类型

- ✅ Node.js CLI 工具
- ✅ TypeScript 库（npm 包）
- ✅ 数据处理工具
- ✅ 后端服务（无框架）
- ❌ React/Vue 前端项目（请用 react-frontend 示例）
- ❌ 多语言项目（请在 modules 中添加多个节点）

## 进阶：添加前端框架

如需添加 React/Vue 支持，修改 `modules.backend.frameworks`：

```json
{
  "modules": {
    "backend": {
      "frameworks": ["react"]
    }
  }
}
```

或新增 frontend 模块：

```json
{
  "modules": {
    "backend": { "path": "src", "languages": ["typescript"], "frameworks": [] },
    "frontend": { "path": "web/src", "languages": ["typescript"], "frameworks": ["react"], "exclude": ["node_modules", "dist"] }
  }
}
```

框架模式会自动从 `config/framework_patterns.json` 加载。

## 相关文档

- [SKILL.md](../../SKILL.md)
- [framework_patterns.json](../../config/framework_patterns.json) — 可用框架列表
- [rule-overrides.md](../../references/rule-overrides.md) — 通用规则豁免指南
