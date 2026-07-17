# Path Resolution Rule

## 触发关键词
getConfigPath, process.cwd, __dirname, import.meta.url, path.resolve, path.join, 路径

## 规则

### PR-1：持久化路径禁用 CWD
**严重级别**：critical

持久化文件路径必须基于固定锚点（import.meta.url / __dirname / 配置的锚点目录），禁止依赖 process.cwd()。

**为什么**：不同启动方式 CWD 不同（IDE 启动 / 命令行启动 / 打包后启动），会导致读写不同文件，造成"数据丢失"假象。

**错误示例**：
```typescript
function getConfigPath(): string {
  return path.resolve(process.cwd(), 'config.json'); // CWD 漂移
}
```

**正确示例**：
```typescript
const SRC_DIR = path.dirname(fileURLToPath(import.meta.url));
const CONFIG_PATH = path.resolve(SRC_DIR, '..', 'config.json');

function getConfigPath(): string {
  // 仅打包模式回退到 CWD（exe 同级目录）
  if (isPackaged) return path.resolve(process.cwd(), 'config.json');
  return CONFIG_PATH;
}
```

### PR-2：路径查找必须有明确优先级
**严重级别**：suggestion

多候选路径时必须明确优先级，并记录在文档中：
1. 用户自定义路径（最高优先级）
2. 打包模式路径（exe 同级）
3. 源码目录路径（开发模式）

### PR-3：路径分隔符跨平台
**严重级别**：best-practice

使用 path.join / path.resolve 而非字符串拼接，确保 Windows/Linux 兼容。

## 检查清单
- [ ] 持久化路径是否依赖 CWD
- [ ] 路径锚点是否基于 import.meta.url / __dirname
- [ ] 多候选路径优先级是否明确
- [ ] 是否使用 path.join 而非字符串拼接