---
name: "cogview-3-flash"
description: "使用智谱 CogView-3-Flash 模型根据文本描述生成图片。当用户要求生成图片、画图、创建视觉内容、AI绘图，或提到 cogview、文生图、图像生成时调用此技能。生成的图片自动下载到工作空间根目录的 ai_image 文件夹。"
---

# CogView-3-Flash 图片生成技能

基于智谱AI开放平台的 CogView-3-Flash 模型，通过文本描述生成高质量图片。

## 何时调用

- 用户明确要求"生成图片"、"画一张图"、"AI绘图"、"文生图"
- 用户提到 `cogview` 或 `cogview-3-flash`
- 用户描述了一个视觉场景并希望得到图像
- 用户需要为网页、UI、博客、海报等生成视觉素材

## 使用方式

执行本技能目录下的生成脚本，并传入 prompt 等参数：

```powershell
node "d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\.trae\skills\cogview-3-flash\generate.js" --prompt "你的描述" --size "1024x1024"
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--prompt` | 是 | - | 图片描述文本（建议结构化：主体+媒介+环境+光线+颜色+情绪+构图） |
| `--size` | 否 | `1024x1024` | 图片尺寸，支持 `1024x1024`、`768x1344`、`1344x768`、`720x1080`、`1080x720` |
| `--quality` | 否 | `standard` | 图片质量，`standard` 或 `hd` |
| `--filename` | 否 | 自动按时间戳生成 | 自定义文件名（不含扩展名） |

## 技术细节

- **API 端点**：`POST https://open.bigmodel.cn/api/paas/v4/images/generations`
- **认证方式**：HTTP Bearer Token（从 `config.json` 读取）
- **API Key 位置**：`config.json` 中的 `api_key` 字段
- **输出目录**：工作空间根目录的 `ai_image/` 文件夹（不存在时自动创建）
- **响应处理**：直接解析同步返回的 `data[0].url`，下载图片到本地

## 提示词工程建议

采用结构化提示词获得更高质量的图像：

1. **主体**：人、动物、建筑、物体等
2. **媒介**：照片、绘画、插图、雕塑、涂鸦等
3. **环境**：竹林、荷塘、沙漠、月球上、水下等
4. **光线**：自然光、体积光、霓虹灯、工作室灯等
5. **颜色**：单色、复色、彩虹色、柔和色等
6. **情绪**：开心、生气、悲伤、惊讶等
7. **构图/角度**：肖像、特写、侧脸图、航拍图等

## 示例

生成一张边牧犬在草地奔跑的图片：

```powershell
node "d:\code\otherProjects\19_Karpathy-AI+Obsidian知识库\.trae\skills\cogview-3-flash\generate.js" --prompt "清晨的阳光照耀下，一只活泼的边牧犬在绿色草地上欢快奔跑，生动的彩色摄影方式，愉快的氛围和明亮的色彩" --size "1344x768"
```

## 错误处理

- API Key 缺失：脚本会报错并提示配置 `config.json`
- 网络错误：重试机制（最多 3 次，指数退避）
- API 错误：直接显示后端返回的 `error.message`
- 下载失败：保留 URL，提示用户手动下载

## 配置文件

`config.json` 结构：

```json
{
  "api_key": "your-api-key-here",
  "base_url": "https://open.bigmodel.cn/api/paas/v4",
  "model": "cogview-3-flash",
  "default_size": "1024x1024",
  "default_quality": "standard",
  "output_dir": "ai_image",
  "max_retries": 3,
  "timeout_ms": 60000
}
```

## 文件清单

- `SKILL.md`：本说明文件
- `config.json`：配置文件（包含 API Key）
- `generate.js`：图片生成脚本
