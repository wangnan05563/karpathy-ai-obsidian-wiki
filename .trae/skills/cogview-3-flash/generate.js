#!/usr/bin/env node
/**
 * CogView-3-Flash 图片生成脚本
 *
 * 通过智谱AI开放平台的 CogView-3-Flash 模型生成图片，
 * 并自动下载到工作空间根目录的 ai_image 文件夹。
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// ============================================================
// 路径解析
// ============================================================
// 脚本位于 .trae/skills/cogview-3-flash/generate.js
// 工作空间根目录 = 脚本向上回溯 4 级
const SCRIPT_DIR = __dirname;
const WORKSPACE_ROOT = path.resolve(SCRIPT_DIR, '..', '..', '..');
const CONFIG_PATH = path.join(SCRIPT_DIR, 'config.json');

// ============================================================
// 配置加载
// ============================================================
function loadConfig() {
  if (!fs.existsSync(CONFIG_PATH)) {
    console.error(`[ERROR] 配置文件不存在: ${CONFIG_PATH}`);
    console.error('请创建 config.json 并填入 api_key。');
    process.exit(1);
  }
  const raw = fs.readFileSync(CONFIG_PATH, 'utf-8');
  let cfg;
  try {
    cfg = JSON.parse(raw);
  } catch (e) {
    console.error(`[ERROR] config.json 解析失败: ${e.message}`);
    process.exit(1);
  }
  if (!cfg.api_key || cfg.api_key === 'your-api-key-here') {
    console.error('[ERROR] config.json 中 api_key 未配置。');
    process.exit(1);
  }
  return cfg;
}

// ============================================================
// 命令行参数解析
// ============================================================
function parseArgs() {
  const args = process.argv.slice(2);
  const opts = {
    prompt: '',
    size: '',
    quality: '',
    filename: '',
  };
  for (let i = 0; i < args.length; i++) {
    const k = args[i];
    const v = args[i + 1];
    if (k === '--prompt') { opts.prompt = v; i++; }
    else if (k === '--size') { opts.size = v; i++; }
    else if (k === '--quality') { opts.quality = v; i++; }
    else if (k === '--filename') { opts.filename = v; i++; }
    else if (k === '--help' || k === '-h') {
      printHelp();
      process.exit(0);
    }
  }
  if (!opts.prompt) {
    console.error('[ERROR] 缺少必填参数 --prompt');
    printHelp();
    process.exit(1);
  }
  return opts;
}

function printHelp() {
  console.log(`
CogView-3-Flash 图片生成脚本

用法:
  node generate.js --prompt "描述" [--size 1024x1024] [--quality standard] [--filename 自定义名]

参数:
  --prompt    必填，图片描述文本
  --size      可选，图片尺寸 (默认: 1024x1024)
              支持: 1024x1024, 768x1344, 1344x768, 720x1080, 1080x720
  --quality   可选，图片质量 (默认: standard)，可选: standard, hd
  --filename  可选，自定义文件名 (不含扩展名)
  --help      显示帮助信息
`);
}

// ============================================================
// HTTP 请求封装
// ============================================================
function request(options, body) {
  return new Promise((resolve, reject) => {
    const req = (options.protocol === 'https:' ? https : http).request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        resolve({ statusCode: res.statusCode, headers: res.headers, body: data });
      });
    });
    req.on('error', reject);
    req.setTimeout(options.timeout || 60000, () => {
      req.destroy(new Error('请求超时'));
    });
    if (body) req.write(body);
    req.end();
  });
}

// ============================================================
// 调用 CogView-3-Flash API（带重试）
// ============================================================
async function callImageAPI(cfg, payload) {
  const url = new URL(cfg.base_url + '/images/generations');
  const bodyStr = JSON.stringify(payload);
  const options = {
    protocol: url.protocol,
    hostname: url.hostname,
    port: url.port || (url.protocol === 'https:' ? 443 : 80),
    path: url.pathname + url.search,
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${cfg.api_key}`,
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(bodyStr),
    },
    timeout: cfg.timeout_ms || 60000,
  };

  const maxRetries = cfg.max_retries || 3;
  let lastErr;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`[INFO] 调用 API (第 ${attempt}/${maxRetries} 次)...`);
      const res = await request(options, bodyStr);
      let parsed;
      try { parsed = JSON.parse(res.body); }
      catch { parsed = { raw: res.body }; }

      if (res.statusCode === 200) {
        return parsed;
      }
      // 4xx 错误通常不应重试（参数问题、鉴权问题）
      if (res.statusCode >= 400 && res.statusCode < 500) {
        const errMsg = parsed.error?.message || parsed.raw || `HTTP ${res.statusCode}`;
        throw new Error(`API 错误 (${res.statusCode}): ${errMsg}`);
      }
      // 5xx 错误可重试
      lastErr = new Error(`API 错误 (${res.statusCode}): ${parsed.error?.message || parsed.raw || ''}`);
    } catch (e) {
      // 网络错误或超时可重试
      if (e.message && e.message.startsWith('API 错误 (4')) throw e;
      lastErr = e;
    }
    if (attempt < maxRetries) {
      const backoff = Math.pow(2, attempt) * 1000;
      console.log(`[WARN] 第 ${attempt} 次失败: ${lastErr.message}，${backoff}ms 后重试...`);
      await new Promise(r => setTimeout(r, backoff));
    }
  }
  throw lastErr || new Error('API 调用失败');
}

// ============================================================
// 下载图片到本地
// ============================================================
function downloadFile(url, destPath, timeoutMs) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https:') ? https : http;
    const req = client.get(url, { timeout: timeoutMs || 120000 }, (res) => {
      // 处理重定向
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        downloadFile(res.headers.location, destPath, timeoutMs).then(resolve, reject);
        return;
      }
      if (res.statusCode !== 200) {
        reject(new Error(`下载失败: HTTP ${res.statusCode}`));
        return;
      }
      const stream = fs.createWriteStream(destPath);
      res.pipe(stream);
      stream.on('finish', () => { stream.close(resolve); });
      stream.on('error', reject);
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(new Error('下载超时')); });
  });
}

// ============================================================
// 主流程
// ============================================================
async function main() {
  const cfg = loadConfig();
  const opts = parseArgs();

  const payload = {
    model: cfg.model || 'cogview-3-flash',
    prompt: opts.prompt,
    size: opts.size || cfg.default_size || '1024x1024',
    quality: opts.quality || cfg.default_quality || 'standard',
  };

  console.log(`[INFO] 模型: ${payload.model}`);
  console.log(`[INFO] 尺寸: ${payload.size}`);
  console.log(`[INFO] 质量: ${payload.quality}`);
  console.log(`[INFO] Prompt: ${payload.prompt}`);

  // 调用 API
  const result = await callImageAPI(cfg, payload);

  // 解析返回结果
  const imageUrl = result.data && result.data[0] && result.data[0].url;
  if (!imageUrl) {
    console.error('[ERROR] API 返回结果中未找到图片 URL');
    console.error(JSON.stringify(result, null, 2));
    process.exit(2);
  }

  console.log(`[INFO] 生成成功，图片 URL: ${imageUrl}`);
  console.log(`[INFO] task_id: ${result.task_id || '-'}`);

  // 下载图片到工作空间根目录的 ai_image 文件夹
  const outputDir = path.join(WORKSPACE_ROOT, cfg.output_dir || 'ai_image');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
    console.log(`[INFO] 创建输出目录: ${outputDir}`);
  }

  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const baseName = opts.filename || `cogview_${ts}`;
  // 从 URL 推断扩展名，默认 .png
  let ext = '.png';
  const urlPath = new URL(imageUrl).pathname;
  const m = urlPath.match(/\.(jpg|jpeg|png|webp|gif)$/i);
  if (m) ext = '.' + m[1].toLowerCase();
  const destPath = path.join(outputDir, baseName + ext);

  console.log(`[INFO] 下载图片到: ${destPath}`);
  try {
    await downloadFile(imageUrl, destPath, cfg.timeout_ms);
    console.log(`[SUCCESS] 图片已保存: ${destPath}`);
    // 输出结构化结果，便于上层调用解析
    console.log(`\n---RESULT---`);
    console.log(JSON.stringify({
      success: true,
      file_path: destPath,
      url: imageUrl,
      task_id: result.task_id || null,
      model: payload.model,
      prompt: payload.prompt,
      size: payload.size,
    }, null, 2));
  } catch (e) {
    console.error(`[ERROR] 下载失败: ${e.message}`);
    console.error(`[INFO] 可手动下载: ${imageUrl}`);
    process.exit(3);
  }
}

main().catch((e) => {
  console.error(`[FATAL] ${e.message}`);
  process.exit(1);
});
