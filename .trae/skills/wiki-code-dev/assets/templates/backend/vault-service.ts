/**
 * Vault 服务模板（文件系统操作）
 * 
 * 关键约束：
 * - 写入路径白名单机制
 * - 路径遍历防护（UUID 正则校验）
 * - 并发文件追加须串行化（withCompileLock）
 * - 部分失败不回滚，标记 draft
 * - 临时文件须用 os.tmpdir() + 唯一前缀
 */

import { readFile, writeFile, mkdir, access, constants } from 'fs/promises';
import { join, resolve } from 'path';

// UUID 正则：用于路径遍历防护
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export interface VaultOptions {
  rootDir: string;
  allowedPaths: string[];
}

/**
 * 编译锁：串行化并发文件追加操作
 */
let compileLock = Promise.resolve<void>();

function withCompileLock<T>(fn: () => Promise<T>): Promise<T> {
  // 并发文件追加须串行化，避免 race condition
  const promise = compileLock.then(fn, fn);
  compileLock = promise.catch(() => {});
  return promise;
}

export class VaultService {
  private rootDir: string;
  private allowedPaths: string[];

  constructor(options: VaultOptions) {
    this.rootDir = options.rootDir;
    this.allowedPaths = options.allowedPaths;
  }

  /**
   * 写入 vault 文件（带白名单 + 路径遍历防护）
   */
  async writeFile(vaultId: string, filePath: string, content: string): Promise<void> {
    // 路径遍历防护：UUID 正则校验
    if (!UUID_REGEX.test(vaultId)) {
      throw new Error(`Invalid vault ID format: ${vaultId}`);
    }

    // 路径解析与白名单检查
    const resolvedPath = resolve(this.rootDir, vaultId, filePath);
    const allowed = this.allowedPaths.some(p => resolvedPath.startsWith(resolve(this.rootDir, p)));

    if (!allowed) {
      throw new Error(`Path traversal detected: ${filePath}`);
    }

    // 确保目录存在（幂等操作）
    await mkdir(join(resolvedPath, '..'), { recursive: true }).catch(() => {});

    // 并发追加串行化
    return withCompileLock(async () => {
      try {
        await writeFile(resolvedPath, content, 'utf-8');
      } catch (err) {
        // 部分失败不回滚，标记 draft
        const draftPath = `${resolvedPath}.draft`;
        await writeFile(draftPath, content, 'utf-8').catch(() => {});
        throw new Error(`Write failed, saved as draft: ${draftPath}`);
      }
    });
  }

  /**
   * 读取 vault 文件
   */
  async readFile(vaultId: string, filePath: string): Promise<string> {
    if (!UUID_REGEX.test(vaultId)) {
      throw new Error(`Invalid vault ID format: ${vaultId}`);
    }

    const resolvedPath = resolve(this.rootDir, vaultId, filePath);
    const allowed = this.allowedPaths.some(p => resolvedPath.startsWith(resolve(this.rootDir, p)));
    if (!allowed) {
      throw new Error(`Path not in whitelist: ${filePath}`);
    }

    try {
      return await readFile(resolvedPath, 'utf-8');
    } catch (err) {
      if ((err as NodeJS.ErrnoException).code === 'ENOENT') {
        return ''; // 文件不存在返回空字符串（幂等读取）
      }
      throw err;
    }
  }

  /**
   * 检查文件是否存在
   */
  async exists(vaultId: string, filePath: string): Promise<boolean> {
    try {
      const resolvedPath = resolve(this.rootDir, vaultId, filePath);
      await access(resolvedPath, constants.F_OK);
      return true;
    } catch {
      return false;
    }
  }
}
