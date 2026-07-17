# 编码规范配置参数

所有规则文件通过引用本文件获取具体参数，禁止在规则文件中硬编码值。

## 路径锚点

| 参数 | 值 | 说明 |
|------|-----|------|
| `path_anchor` | `import.meta.url` | ESM 项目路径解析首选锚点 |
| `path_anchor_cjs` | `__dirname` | CJS 项目路径解析锚点 |
| `packaged_marker` | `process.pkg` | 打包模式检测标识 |
| `config_filename` | `config.json` | 配置文件名 |

## 缓存参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `cache_ttl_ms` | `30000` | 内存缓存默认 TTL（30 秒） |
| `cache_refresh_required` | `true` | 写盘后必须刷新缓存 |

## 白名单正则

| 参数 | 值 | 用途 |
|------|-----|-----|
| `uuid_regex` | `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$` | UUID 文件名校验 |
| `safe_filename_regex` | `^[a-zA-Z0-9_-]+$` | 通用安全文件名 |
| `safe_path_regex` | `^[a-zA-Z0-9_/-]+$` | 通用安全相对路径 |

## 存储边界

| 参数 | 值 | 说明 |
|------|-----|-----|
| `browser_storage_lifetime` | `per-origin` | localStorage/IndexedDB 按 origin 隔离 |
| `cross_origin_strategy` | `backend-persistence` | 跨 origin 数据用后端持久化 |
| `cache_fallback_enabled` | `true` | 浏览器存储作为后端降级缓存 |

## 降级策略

| 参数 | 值 | 说明 |
|------|-----|-----|
| `backend_unavailable_action` | `fallback-to-cache` | 后端不可用时降级到本地缓存 |
| `cache_unavailable_action` | `non-blocking` | 缓存不可用不阻断主流程 |
| `silent_failure_layers` | `cache-write,indexdb-write` | 静默失败的层（不抛错） |

## 单一权威源

| 参数 | 值 | 说明 |
|------|-----|-----|
| `authoritative_source_config` | `backend config.json` | 配置类数据权威源 |
| `authoritative_source_session` | `backend data/` | 会话类数据权威源 |
| `allowed_cache_layers` | `localStorage,IndexedDB,memory` | 允许的缓存层 |

## 编码

| 参数 | 值 | 说明 |
|------|-----|-----|
| `source_encoding` | `utf-8-no-bom` | 源文件编码 |
| `meta_encoding` | `utf-8-no-bom` | meta 文件编码 |
| `bat_encoding` | `ascii-no-bom` | .bat 文件编码（cmd.exe 兼容） |

## 编码守卫参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `encoding_detection_method` | `utf8-strict-decode` | 严格 UTF-8 解码检测（UTF8Encoding(false, true)） |
| `encoding_fallback` | `gb2312` | 非 UTF-8 文件的回退编码（Windows 中文环境） |
| `encoding_scan_command` | `node scripts/check-encoding.js` | 编码扫描命令 |
| `encoding_fix_command` | `node scripts/check-encoding.js --fix` | 编码修复命令 |
| `encoding_scan_scope` | `source + meta-config` | 扫描范围（源码 + 元配置文件） |

## PowerShell 环境约束

| 参数 | 值 | 说明 |
|------|-----|------|
| `command_separator` | `;` | 命令分隔符（不支持 &&） |
| `readonly_vars` | `$pid,$PWD,$HOME` | 只读变量列表（禁止赋值） |
| `cwd_param` | `cwd` | RunCommand 工作目录参数名 |
| `blocked_commands` | `cmd /c` | 被安全策略阻止的命令 |

## bat 脚本约束

| 参数 | 值 | 说明 |
|------|-----|------|
| `bat_encoding` | `ascii-no-bom` | .bat 文件编码（cmd.exe 兼容） |
| `bat_pause_issue` | `true` | bat 脚本末尾 pause 会卡住自动化 |
| `bat_alternative` | `npm run` | 直接用 npm 命令替代 bat 脚本 |

## 适配新项目

修改本文件中的参数值即可适配不同项目：
- 路径锚点：根据模块系统选择 `import.meta.url` 或 `__dirname`
- 缓存 TTL：根据业务实时性要求调整
- 白名单正则：根据 ID 生成策略选择 UUID/ULID/Snowflake
- 权威源：根据架构选择 `backend`/`file`/`database`
- 编码回退：根据系统区域选择 `gb2312`/`gbk`/`shift-jis` 等
- 命令分隔符：PowerShell 用 `;`，bash 用 `&&`