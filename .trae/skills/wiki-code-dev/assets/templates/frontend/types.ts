/**
 * 类型定义模板
 * 
 * 关键约束：
 * - TypeScript strict 模式
 * - 联合类型窄化须使用 type guard 或 as 断言
 * - fetch 响应类型须明确定义
 */

// ===== SSE 事件类型 =====

/** SSE 事件通用接口 */
export interface SSEEvent<T = unknown> {
  /** 事件类型：progress / page / done / error */
  type: string;
  /** 事件数据 */
  data: T;
  /** 时间戳 */
  timestamp: number;
}

/** 编译进度事件数据 */
export interface CompileProgressData {
  status: 'processing' | 'generating' | 'saving';
  page?: number;
  totalPages?: number;
  message: string;
}

/** 编译完成事件数据 */
export interface CompileDoneData {
  status: 'complete' | 'partial';
  pages: number;
  words: number;
  duration: number;
  reason?: string;
}

/** 编译错误事件数据 */
export interface CompileErrorData {
  status: 'error';
  message: string;
  code?: string;
}

/** 编译状态联合类型 */
export type CompileState =
  | { status: 'idle' }
  | { status: 'compiling'; events: SSEEvent[]; currentVaultId: string; currentTopic: string; lastError: null }
  | { status: 'done'; events: SSEEvent[]; currentVaultId: string; currentTopic: string; lastError: null }
  | { status: 'error'; events: SSEEvent[]; currentVaultId: string; currentTopic: string; lastError: string };

// ===== 类型窄化守卫 =====

/**
 * 判断是否为进度事件
 * TS 无法基于独立 discriminant 窄化，需用 type guard 函数
 */
export function isProgressEvent(event: SSEEvent): event is SSEEvent<CompileProgressData> {
  return event.type === 'progress';
}

/**
 * 判断是否为完成事件
 */
export function isDoneEvent(event: SSEEvent): event is SSEEvent<CompileDoneData> {
  return event.type === 'done';
}

/**
 * 判断是否为错误事件
 */
export function isErrorEvent(event: SSEEvent): event is SSEEvent<CompileErrorData> {
  return event.type === 'error';
}

// ===== API 响应类型 =====

/** 通用 fetch 响应包装 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    message: string;
    code: string;
  };
}

/** Vault 信息 */
export interface VaultInfo {
  id: string;
  name: string;
  path: string;
  lastModified: string;
  fileCount: number;
}

/** Wiki 页面 */
export interface WikiPage {
  id: string;
  title: string;
  content: string;
  vaultId: string;
  createdAt: string;
  updatedAt: string;
  tags: string[];
}

// ===== 参数类型 =====

/** 编译请求参数 */
export interface CompileRequestParams {
  vaultId: string;
  topic?: string;
}

/** SSE 消费者配置 */
export interface SSEConsumerConfig {
  signal?: AbortSignal;
  onEvent: (event: SSEEvent) => void;
  onError: (err: Error) => void;
  onEnd?: () => void;
}
