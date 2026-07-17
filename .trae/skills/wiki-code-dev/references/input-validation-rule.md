# Input Validation Rule

## 触发关键词
request.params, request.body, path.join, fs.readFile, 用户输入, 文件名

## 规则

### IV-1：用户输入作文件名必须白名单校验
**严重级别**：critical

用户输入作为文件名/路径组成部分时，必须用白名单正则校验，禁止直接 path.join 拼接。

**为什么**：未校验的输入会导致路径穿越攻击（如 ../../etc/passwd）。

**错误示例**：
```typescript
app.get('/api/files/:name', (req, res) => {
  const filePath = path.join(dataDir, req.params.name); // 路径穿越风险
  fs.readFile(filePath, ...);
});
```

**正确示例**：
```typescript
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

app.get('/api/files/:id', (req, res) => {
  const { id } = req.params;
  if (!UUID_RE.test(id)) {
    return res.code(400).send({ error: '无效的 ID' });
  }
  const filePath = path.join(dataDir, `${id}.json`);
  // ...
});
```

### IV-2：URL 编码的路径穿越必须防护
**严重级别**：critical

攻击者会用 URL 编码绕过：`..%2F..%2F` 解码后是 `../../`。Fastify 路由参数会自动解码，UUID 正则可同时拦截。

### IV-3：白名单正则必须在 config 中管理
**严重级别**：suggestion

不同业务用不同 ID 策略（UUID/ULID/Snowflake），白名单正则必须在 config 中可配置：
```yaml
input_validation:
  id_regex: "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
  safe_filename_regex: "^[a-zA-Z0-9_-]+$"
```

### IV-4：文件扩展名必须固定
**严重级别**：suggestion

服务端生成的文件扩展名必须固定（如 .json），禁止使用用户输入的扩展名。

## 检查清单
- [ ] 用户输入作文件名是否有白名单校验
- [ ] URL 编码路径穿越是否防护
- [ ] 白名单正则是否在 config 可配置
- [ ] 文件扩展名是否服务端固定