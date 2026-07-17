# Rule Catalog - SSE Streaming Output

## Scope
- Covers: Fastify routes returning event streams as \	ext/event-stream\, including headers, event writing, connection lifecycle management, error pushing methods.
- Applies to: long-task routes (compile, query, batch generation), eply.raw.write\ related code, SSE helper functions.

## Rules

### SSE headers must be complete with X-Accel-Buffering
- Category: correctness | Severity: critical
- Description: SSE responses must set complete headers, otherwise Nginx/proxy buffering prevents real-time event delivery. In addition to standard \Content-Type\ / \Cache-Control\ / \Connection\, must explicitly set \X-Accel-Buffering: no\ to bypass Nginx response buffering.
- Suggested fix: Set all headers at once before writing the first event, fixed order to avoid omissions.
- Example (Bad):
  \\	ypescript
  // Only sets Content-Type, missing Cache-Control / Connection / X-Accel-Buffering
  reply.raw.writeHead(200, { 'Content-Type': 'text/event-stream' });
  \- Example (Good):
  \\	ypescript
  reply.raw.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no',
  });
  \
### Event format must be event + data double-line + \\n\\n separator
- Category: correctness | Severity: critical
- Description: SSE protocol requires events separated by blank lines (\\
\\n\); each event must include an \event:\ line identifying the type and a \data:\ line carrying single-line JSON serialization. Multi-line JSON or missing \event:\ field causes client parsing failure.
- Suggested fix: Encapsulate a unified \send\ helper function that enforces event/data pairing and handles separator concatenation.

### Must close reply.raw.end() in finally
- Category: reliability | Severity: critical
- Description: SSE connections are long-lived. Without eply.raw.end()\ in finally, both exception paths and normal completion cause connection leaks and infinite client waits. The \done\ event alone is insufficient to close the transport layer.
- Suggested fix: Wrap streaming logic in \	ry/finally\, unconditionally call eply.raw.end()\ in finally.
- Example (Bad):
  \\	ypescript
  // Missing finally - if adapter.run() throws, connection never closes
  for await (const ev of adapter.run()) { send(reply.raw, ev.type, ev.data); }
  \
### Errors must be pushed via error event, not thrown to break connection
- Category: reliability | Severity: critical
- Description: Uncaught exceptions in SSE streams are caught by Fastify and written as non-SSE format (e.g., JSON error), causing inevitable client parse failure and loss of produced event context. Errors should be pushed as \error\ events, letting the client decide whether to retry.
- Suggested fix: Catch exceptions inside try block, first \send(reply.raw, 'error', { message })\, then close in finally.
- Example (Good):
  \\	ypescript
  try {
    for await (const ev of adapter.run()) { send(reply.raw, ev.type, ev.data); }
  } catch (err) {
    send(reply.raw, 'error', { message: err instanceof Error ? err.message : String(err) });
  } finally { reply.raw.end(); }
  \
### SSE routes must not use return reply.send()
- Category: correctness | Severity: critical
- Description: SSE routes have already taken over the underlying response stream via eply.raw.writeHead\. Calling eply.send()\ or eturn reply.send()\ causes Fastify to attempt writing the response body again, resulting in \ERR_STREAM_ALREADY_FINISHED\ or response body overwrite.
- Suggested fix: SSE route handlers must not return any value (return void or Promise<void>); all output via eply.raw.write\.

### Event writes should be unified into a send helper function
- Category: maintainability | Severity: suggestion
- Description: Multiple places directly concatenating event/data/separator strings leads to format inconsistency (missing separators, unserialized JSON). A unified \send(raw, event, data)\ centralizes the event format contract and reduces errors.
- Suggested fix: Provide a single \send\ function at routes同级 or utils level; all SSE routes reuse it.
- Example (Good):
  \\	ypescript
  // utils/sse.ts - single point encapsulation
  export function send(raw: NodeJS.WritableStream, event: string, data: unknown): void {
    raw.write(\event: \\ndata: \\n\
\);
  }
  \