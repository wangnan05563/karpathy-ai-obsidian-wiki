/**
 * 工作流模板（Harness 集成 + AsyncIterable 事件流）
 * 
 * 关键约束：
 * - 必须实现 EngineAdapter 接口，完整 yield 事件
 * - 预算超限须返回部分结果而非中断
 * - Hook 须注册确定性逻辑
 * - Prompt 须单点存储
 */

import type { EngineAdapter, WorkflowEvent, HookRegistry } from '@wiki/harness';

export interface CompileParams {
  vaultId: string;
  topic?: string;
}

export interface CompileResult {
  pages: number;
  words: number;
  duration: number;
}

/**
 * 编译工作流：通过 harness 驱动 LLM 生成 wiki 页面
 */
export async function* compileWorkflow(params: CompileParams): AsyncIterable<WorkflowEvent> {
  // 获取 prompt 模板（单点存储）
  const prompt = getPromptTemplate('compile', params.topic);

  // 初始化 harness 适配器
  const adapter: EngineAdapter = {
    // tool-loop: 工具调用循环
    async executeTool(toolName: string, args: Record<string, unknown>) {
      switch (toolName) {
        case 'read_vault':
          return await readVaultFile(args.vaultId as string, args.path as string);
        case 'write_vault':
          return await writeVaultFile(args.vaultId as string, args.content as string);
        case 'search_wiki':
          return await searchWiki(args.query as string);
        default:
          throw new Error(`Unknown tool: ${toolName}`);
      }
    },

    // state: 状态管理
    getState(): Record<string, unknown> {
      return { vaultId: params.vaultId, topic: params.topic };
    },

    // retry: 重试策略
    shouldRetry(err: Error, attempt: number): boolean {
      if (attempt >= 3) return false;
      return err.message.includes('timeout') || err.message.includes('rate_limit');
    },

    // budget: 预算控制
    budget: {
      maxTokens: 50000,
      maxCost: 0.10,
      currency: 'USD'
    },

    // hook: 钩子注册
    hooks: createHooks()
  };

  // 驱动 harness 执行
  const harness = new Harness(adapter);
  let eventIndex = 0;

  try {
    for await (const result of harness.run(prompt)) {
      // AsyncIterable 事件流须正确 yield
      yield {
        type: ['progress', 'page', 'done'][Math.min(eventIndex++, 2)] || 'done',
        data: result,
        timestamp: Date.now()
      };
    }
  } catch (err) {
    // 预算超限须返回部分结果而非中断
    if (err.message.includes('budget exceeded')) {
      yield {
        type: 'done',
        data: { status: 'partial', reason: 'budget_exceeded' },
        timestamp: Date.now()
      };
    } else {
      throw err;
    }
  }
}

function getPromptTemplate(type: string, topic?: string): string {
  // Prompt 单点存储：从 prompts/ 目录读取
  const templates: Record<string, string> = {
    compile: `编译 wiki 页面。主题：${topic || '默认'}`,
    query: '查询 wiki 知识'
  };
  return templates[type] || '';
}

function createHooks(): HookRegistry {
  return {
    // Hook 注册确定性逻辑
    onToolCall: (name: string, args: unknown) => {
      console.log(`[hook] tool_call: ${name}`, args);
    },
    onBudgetWarning: (usage: number, limit: number) => {
      console.warn(`[hook] budget warning: ${usage}/${limit}`);
    },
    onComplete: (result: unknown) => {
      console.log('[hook] complete', result);
    }
  };
}

async function readVaultFile(vaultId: string, path: string): Promise<string> {
  // 实际实现调用 vault service
  throw new Error('Not implemented');
}

async function writeVaultFile(vaultId: string, content: string): Promise<void> {
  throw new Error('Not implemented');
}

async function searchWiki(query: string): Promise<Array<{ title: string; snippet: string }>> {
  throw new Error('Not implemented');
}
