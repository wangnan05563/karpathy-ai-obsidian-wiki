/**
 * Fastify SSE 路由模板
 * 
 * 关键约束：
 * - SSE 路由必须使用 reply.raw.write() 逐块写入，禁止 return reply.send()
 * - 必须设置完整的 SSE headers（Content-Type/Cache-Control/Connection/X-Accel-Buffering）
 * - finally 中必须调用 reply.raw.end() 确保连接关闭
 */

import type { FastifyInstance, FastifyReply } from 'fastify';

export async function registerWikiRoute(app: FastifyInstance) {
  // SSE 路由：Content-Type 必须为 text/event-stream
  app.get('/api/wiki/compile', {
    // 参数校验 schema
    schema: {
      querystring: {
        type: 'object',
        required: ['vaultId'],
        properties: {
          vaultId: { type: 'string' },
          topic: { type: 'string' }
        }
      }
    }
  }, async (request, reply) => {
    const { vaultId, topic } = request.query as { vaultId: string; topic?: string };

    // SSE headers 设置（必须完整）
    reply.raw.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no'
    });

    let stream: AsyncIterable<any> | null = null;

    try {
      // 创建工作流实例
      stream = await compileWorkflow({ vaultId, topic });

      // 消费事件流，转发到 SSE 客户端
      for await (const event of stream) {
        const payload = JSON.stringify(event.data);
        const sseLine = event.type
          ? `event: ${event.type}\ndata: ${payload}\n\n`
          : `data: ${payload}\n\n`;
        reply.raw.write(sseLine);
      }

      // 正常完成
      reply.raw.write('event: done\ndata: {"status":"complete"}\n\n');
    } catch (err) {
      // 错误必须通过 error 事件推送，不能直接 throw
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      reply.raw.write(`event: error\ndata: {"status":"error","message":"${errorMsg}"}\n\n`);
    } finally {
      // 必须关闭连接
      reply.raw.end();
    }
  });
}
