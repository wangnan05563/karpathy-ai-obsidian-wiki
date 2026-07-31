---
name: "cogvideox-flash"
description: "使用智谱 CogVideoX-Flash 模型根据文本描述生成视频。当用户要求生成视频、创建动态画面、AI视频，或提到 cogvideox、文生视频、视频生成时调用此技能。生成的视频自动下载到工作空间根目录的 ai_video 文件夹，并落盘 result.json 元信息。"
---

# CogVideoX-Flash 视频生成技能

基于智谱AI开放平台的 CogVideoX-Flash 模型，通过文本描述生成视频。采用异步任务工作流：提交任务 → 轮询状态 → 下载视频。

## 何时调用

- 用户明确要求"生成视频"、"做一段视频"、"AI视频"、"文生视频"
- 用户提到 `cogvideox` 或 `cogvideox-flash`
- 用户描述了一个动态场景并希望得到视频
- 用户需要为网页、演示、广告等生成动态视频素材

## 使用方式

执行本技能目录下的生成脚本，并传入 prompt 等参数：

```powershell
node "d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\.trae\skills\cogvideox-flash\generate.js" --prompt "你的描述" --size "1920x1080"
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--prompt` | 是 | - | 视频描述文本 |
| `--size` | 否 | `1920x1080` | 视频分辨率，支持 `1920x1080`、`1080x1920`、`1280x720` |
| `--quality` | 否 | `standard` | 视频质量，`standard` 或 `hd` |
| `--with_audio` | 否 | `true` | 是否生成音频（原生支持音视频同步） |
| `--filename` | 否 | 自动按时间戳生成 | 自定义文件名（不含扩展名） |
| `--poll_interval` | 否 | `10` | 轮询间隔（秒） |
| `--max_poll` | 否 | `60` | 最大轮询次数（默认 60 次 × 10 秒 = 10 分钟） |

## 技术细节

- **API 端点**：
  - 提交任务：`POST https://open.bigmodel.cn/api/paas/v4/videos/generations`
  - 查询结果：`GET https://open.bigmodel.cn/api/paas/v4/async-result/{task_id}`
- **认证方式**：HTTP Bearer Token（从 `config.json` 读取）
- **API Key 位置**：`config.json` 中的 `api_key` 字段
- **输出目录**：工作空间根目录的 `ai_video/` 文件夹（不存在时自动创建）
- **任务状态**：`PROCESSING`（处理中）→ `SUCCESS`（成功）/ `FAIL`（失败）
- **元信息落盘**：每次生成都会在 `ai_video/` 目录写入 `result.json`，记录任务 ID、URL、本地路径等

## 工作流

1. **提交任务**：调用 `POST /videos/generations`，获得 `task_id` 和初始 `task_status`
2. **轮询状态**：每隔 `poll_interval` 秒调用 `GET /async-result/{task_id}` 查询
3. **任务完成**：`task_status === SUCCESS` 时返回 `video_result` 数组，包含视频 URL 和封面图 URL
4. **下载视频**：将视频下载到 `ai_video/` 文件夹
5. **落盘元信息**：写入 `result.json`

## 提示词建议

- 描述具体的动作和场景变化，而非静态画面
- 控制镜头运动：推、拉、摇、移、跟
- 指定时长感（短动作 vs 连续场景）
- 示例："一架飞机在空中旋转，云层从画面左侧飘过，阳光从右侧照射"

## 示例

生成一段猫咪玩球的视频：

```powershell
node "d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\.trae\skills\cogvideox-flash\generate.js" --prompt "一只小猫在草地上玩彩色的球，球滚来滚去，小猫追着跑，阳光明媚" --size "1920x1080"
```

## 错误处理

- API Key 缺失：脚本会报错并提示配置 `config.json`
- 任务失败：`task_status === FAIL` 时显示失败原因
- 轮询超时：超过 `max_poll` 次仍为 `PROCESSING` 时退出，提示用户稍后用 task_id 查询
- 下载失败：保留 URL，提示用户手动下载

## 配置文件

`config.json` 结构：

```json
{
  "api_key": "your-api-key-here",
  "base_url": "https://open.bigmodel.cn/api/paas/v4",
  "model": "cogvideox-flash",
  "default_size": "1920x1080",
  "default_quality": "standard",
  "default_with_audio": true,
  "output_dir": "ai_video",
  "max_retries": 3,
  "timeout_ms": 60000,
  "poll_interval_sec": 10,
  "max_poll_count": 60
}
```

## 文件清单

- `SKILL.md`：本说明文件
- `config.json`：配置文件（包含 API Key）
- `generate.js`：视频生成脚本（异步任务 + 轮询 + 下载）
