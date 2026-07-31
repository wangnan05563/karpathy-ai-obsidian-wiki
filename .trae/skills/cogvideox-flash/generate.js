#!/usr/bin/env node
/**
 * CogVideoX-Flash 视频生成脚本
 *
 * 采用异步任务工作流：
 *   1. 提交任务 → POST /videos/generations，获得 task_id
 *   2. 轮询状态 → GET /async-result/{task_id}
 *   3. 任务完成 → 下载视频到 ai_video 文件夹
 *   4. 落盘元信息 → result.json
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// ============================================================
// 路径解析
// ============================================================
// 脚本位于 .trae/skills/cogvideox-flash/generate.js
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
    with_audio: '',
    filename: '',
    poll_interval: '',
    max_poll: '',
  };
  for (let i = 0; i < args.length; i++) {
    const k = args[i];
    const v = args[i + 1];
    if (k === '--prompt') { opts.prompt = v; i++; }
    else if (k === '--size') { opts.size = v; i++; }
    else if (k === '--quality') { opts.quality = v; i++; }
    else if (k === '--with_audio') { opts.with_audio = v; i++; }
    else if (k === '--filename') { opts.filename = v; i++; }
    else if (k === '--poll_interval') { opts.poll_interval = v; i++; }
    else if (k === '--max_poll') { opts.max_poll = v; i++; }
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
CogVideoX-Flash 视频生成脚本

用法:
  node generate.js --prompt "描述" [--size 1920x1080] [--quality standard] [--with_audio true]

参数:
  --prompt         必填，视频描述文本
  --size           可选，视频分辨率 (默认: 1920x1080)
                   支持: 1920x1080, 1080x1920, 1280x720
  --quality        可选，视频质量 (默认: standard)，可选: standard, hd
  --with_audio     可选，是否生成音频 (默认: true)
  --filename       可选，自定义文件名 (不含扩展名)
  --poll_interval  可选，轮询间隔秒数 (默认: 10)
  --max_poll       可选，最大轮询次数 (默认: 60)
  --help           显示帮助信息
`);
}

// ============================================================
// HTTP 请求封装
// ============================================================
function httpRequest(method, urlStr, headers, body, timeoutMs) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlStr);
    const isHttps = url.protocol === 'https:';
    const options = {
      protocol: url.protocol,
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname + url.search,
      method: method,
      headers: headers || {},
      timeout: timeoutMs || 60000,
    };
    const req = (isHttps ? https : http).request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        resolve({ statusCode: res.statusCode, headers: res.headers, body: data });
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(new Error('请求超时')); });
    if (body) req.write(body);
    req.end();
  });
}

// ============================================================
// 提交视频生成任务（带重试）
// ============================================================
async function submitTask(cfg, payload) {
  const url = cfg.base_url + '/videos/generations';
  const bodyStr = JSON.stringify(payload);
  const headers = {
    'Authorization': `Bearer ${cfg.api_key}`,
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(bodyStr),
  };

  const maxRetries = cfg.max_retries || 3;
  let lastErr;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`[INFO] 提交任务 (第 ${attempt}/${maxRetries} 次)...`);
      const res = await httpRequest('POST', url, headers, bodyStr, cfg.timeout_ms);
      let parsed;
      try { parsed = JSON.parse(res.body); }
      catch { parsed = { raw: res.body }; }

      if (res.statusCode === 200) {
        return parsed;
      }
      if (res.statusCode >= 400 && res.statusCode < 500) {
        const errMsg = parsed.error?.message || parsed.raw || `HTTP ${res.statusCode}`;
        throw new Error(`提交失败 (${res.statusCode}): ${errMsg}`);
      }
      lastErr = new Error(`提交失败 (${res.statusCode}): ${parsed.error?.message || parsed.raw || ''}`);
    } catch (e) {
      if (e.message && e.message.startsWith('提交失败 (4')) throw e;
      lastErr = e;
    }
    if (attempt < maxRetries) {
      const backoff = Math.pow(2, attempt) * 1000;
      console.log(`[WARN] 第 ${attempt} 次失败: ${lastErr.message}，${backoff}ms 后重试...`);
      await new Promise(r => setTimeout(r, backoff));
    }
  }
  throw lastErr || new Error('提交任务失败');
}

// ============================================================
// 查询任务结果
// ============================================================
async function queryTask(cfg, taskId) {
  const url = `${cfg.base_url}/async-result/${taskId}`;
  const headers = {
    'Authorization': `Bearer ${cfg.api_key}`,
  };
  const res = await httpRequest('GET', url, headers, null, cfg.timeout_ms);
  let parsed;
  try { parsed = JSON.parse(res.body); }
  catch { parsed = { raw: res.body }; }
  if (res.statusCode !== 200) {
    throw new Error(`查询失败 (${res.statusCode}): ${parsed.error?.message || parsed.raw || ''}`);
  }
  return parsed;
}

// ============================================================
// 轮询任务状态
// ============================================================
async function pollTask(cfg, taskId, opts) {
  const interval = (opts.poll_interval ? parseInt(opts.poll_interval, 10) : cfg.poll_interval_sec) * 1000;
  const maxPoll = opts.max_poll ? parseInt(opts.max_poll, 10) : (cfg.max_poll_count || 60);

  console.log(`[INFO] 开始轮询任务状态，间隔 ${interval / 1000}s，最多 ${maxPoll} 次...`);

  for (let i = 1; i <= maxPoll; i++) {
    const result = await queryTask(cfg, taskId);
    const status = result.task_status;

    if (status === 'SUCCESS') {
      console.log(`[INFO] 任务成功 (第 ${i} 次轮询)`);
      return result;
    }
    if (status === 'FAIL') {
      console.error(`[ERROR] 任务失败 (第 ${i} 次轮询)`);
      console.error(JSON.stringify(result, null, 2));
      throw new Error(`视频生成失败: ${JSON.stringify(result)}`);
    }

    // PROCESSING 或其他状态，继续等待
    process.stdout.write(`[INFO] 状态: ${status} (第 ${i}/${maxPoll} 次)，等待 ${interval / 1000}s...\r`);
    await new Promise(r => setTimeout(r, interval));
  }

  // 超过最大轮询次数
  throw new Error(`轮询超时: 任务 ${taskId} 在 ${maxPoll} 次轮询后仍未完成。可用 task_id 手动查询: GET ${cfg.base_url}/async-result/${taskId}`);
}

// ============================================================
// 下载文件（视频或图片）
// ============================================================
function downloadFile(url, destPath, timeoutMs) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https:') ? https : http;
    const req = client.get(url, { timeout: timeoutMs || 300000 }, (res) => {
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
// 从 URL 推断扩展名
// ============================================================
function inferExt(url, defaultExt) {
  try {
    const urlPath = new URL(url).pathname;
    const m = urlPath.match(/\.(mp4|mov|avi|mkv|webm|jpg|jpeg|png|webp|gif)$/i);
    if (m) return '.' + m[1].toLowerCase();
  } catch {}
  return defaultExt;
}

// ============================================================
// 主流程
// ============================================================
async function main() {
  const cfg = loadConfig();
  const opts = parseArgs();

  const withAudio = opts.with_audio !== undefined
    ? (opts.with_audio === 'true' || opts.with_audio === '1')
    : (cfg.default_with_audio !== undefined ? cfg.default_with_audio : true);

  const payload = {
    model: cfg.model || 'cogvideox-flash',
    prompt: opts.prompt,
    size: opts.size || cfg.default_size || '1920x1080',
    quality: opts.quality || cfg.default_quality || 'standard',
    with_audio: withAudio,
  };

  console.log(`[INFO] 模型: ${payload.model}`);
  console.log(`[INFO] 尺寸: ${payload.size}`);
  console.log(`[INFO] 质量: ${payload.quality}`);
  console.log(`[INFO] 音频: ${payload.with_audio}`);
  console.log(`[INFO] Prompt: ${payload.prompt}`);

  // 步骤 1：提交任务
  const submitResult = await submitTask(cfg, payload);
  const taskId = submitResult.id;
  if (!taskId) {
    console.error('[ERROR] 提交任务返回结果中未找到 task id');
    console.error(JSON.stringify(submitResult, null, 2));
    process.exit(2);
  }
  console.log(`[INFO] 任务已提交，task_id: ${taskId}`);
  console.log(`[INFO] 初始状态: ${submitResult.task_status || 'PROCESSING'}`);
  console.log(`[INFO] request_id: ${submitResult.request_id || '-'}`);

  // 步骤 2：轮询任务状态
  const finalResult = await pollTask(cfg, taskId, opts);

  // 步骤 3：解析视频结果
  const videoResults = finalResult.video_result || [];
  if (!videoResults.length) {
    console.error('[ERROR] 任务成功但未返回视频结果');
    console.error(JSON.stringify(finalResult, null, 2));
    process.exit(2);
  }

  const videoUrl = videoResults[0].url;
  const coverUrl = videoResults[0].cover_image_url;
  if (!videoUrl) {
    console.error('[ERROR] 视频结果中未找到 URL');
    console.error(JSON.stringify(videoResults[0], null, 2));
    process.exit(2);
  }

  console.log(`[INFO] 视频生成成功`);
  console.log(`[INFO] 视频 URL: ${videoUrl}`);
  if (coverUrl) console.log(`[INFO] 封面 URL: ${coverUrl}`);

  // 步骤 4：下载视频到工作空间根目录的 ai_video 文件夹
  const outputDir = path.join(WORKSPACE_ROOT, cfg.output_dir || 'ai_video');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
    console.log(`[INFO] 创建输出目录: ${outputDir}`);
  }

  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const baseName = opts.filename || `cogvideox_${ts}`;
  const videoExt = inferExt(videoUrl, '.mp4');
  const videoPath = path.join(outputDir, baseName + videoExt);

  console.log(`[INFO] 下载视频到: ${videoPath}`);
  let videoDownloaded = false;
  try {
    await downloadFile(videoUrl, videoPath, 300000);
    console.log(`[SUCCESS] 视频已保存: ${videoPath}`);
    videoDownloaded = true;
  } catch (e) {
    console.error(`[ERROR] 视频下载失败: ${e.message}`);
    console.error(`[INFO] 可手动下载: ${videoUrl}`);
  }

  // 下载封面图（如有）
  let coverPath = null;
  if (coverUrl) {
    const coverExt = inferExt(coverUrl, '.jpg');
    const coverCandidate = path.join(outputDir, baseName + '_cover' + coverExt);
    try {
      await downloadFile(coverUrl, coverCandidate, 60000);
      coverPath = coverCandidate;
      console.log(`[SUCCESS] 封面已保存: ${coverPath}`);
    } catch (e) {
      console.error(`[WARN] 封面下载失败: ${e.message}`);
    }
  }

  // 步骤 5：落盘元信息 result.json
  const resultInfo = {
    success: videoDownloaded,
    task_id: taskId,
    request_id: finalResult.request_id || submitResult.request_id || null,
    model: payload.model,
    prompt: payload.prompt,
    size: payload.size,
    quality: payload.quality,
    with_audio: payload.with_audio,
    video_url: videoUrl,
    cover_url: coverUrl || null,
    video_path: videoDownloaded ? videoPath : null,
    cover_path: coverPath,
    task_status: finalResult.task_status,
    created_at: new Date().toISOString(),
  };
  const resultPath = path.join(outputDir, 'result.json');

  // 合并历史记录（若 result.json 已存在）
  let history = [];
  if (fs.existsSync(resultPath)) {
    try {
      const old = JSON.parse(fs.readFileSync(resultPath, 'utf-8'));
      if (Array.isArray(old)) history = old;
      else history = [old];
    } catch {}
  }
  history.push(resultInfo);
  fs.writeFileSync(resultPath, JSON.stringify(history, null, 2), 'utf-8');
  console.log(`[INFO] 元信息已写入: ${resultPath}`);

  // 输出结构化结果
  console.log(`\n---RESULT---`);
  console.log(JSON.stringify(resultInfo, null, 2));

  if (!videoDownloaded) process.exit(3);
}

main().catch((e) => {
  console.error(`[FATAL] ${e.message}`);
  process.exit(1);
});
