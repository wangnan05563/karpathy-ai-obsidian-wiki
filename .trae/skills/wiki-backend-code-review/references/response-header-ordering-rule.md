# Response Header Ordering Rule（响应头时序：成功读取后再设置）

## 触发关键词

Content-Disposition, Content-Type, reply.header, 下载, download, 流式, 附件,
响应头, 头时序, 半截响应, 错误路径, 成功路径, 文件流出

## 规则

### BR-100-1（major）：Content-Disposition / Content-Type 须在「成功读取后、send 前」设置

「先读文件、再发附件响应」的 handler，`reply.header('Content-Disposition', ...)` 须放在
成功读取之后、`reply.send` 之前。读取失败分支不得提前设这些头。

### BR-100-2（major）：错误路径只置状态码与错误体，绝不携带 Content-Disposition

`catch` 只应 `reply.code(status).send({ error })`；错误响应不得带 `attachment` 头，
否则客户端（尤其移动端）会把它当「损坏的下载文件」而非「错误提示」，误导且难排查。

> 对应 wiki-code-dev **CODING-RESP-HEADER-ORDER / RH-1~RH-2**；
> 与 **BR-097（鉴权门）**、**BR-099（错误码透传）** 协同——错误路径同时要保证正确状态码且无附件头。

## 检查清单

- [ ] 响应头（Content-Disposition / Content-Type）是否在成功读取后、send 前设置
- [ ] 错误（catch）分支是否只置状态码 + 错误体，不携带 Content-Disposition
- [ ] 是否无「先 set 头、后可能抛错」的半截响应路径
- [ ] 二进制与文本分支是否都遵循同一头时序约定
