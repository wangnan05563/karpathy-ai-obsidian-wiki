# wiki-* 技能 Token 审计工具

> 独立扫描脚本 + 预算配置，用于监控四个 wiki-* 技能的 token 使用效率，防止文件膨胀回涨。
> 本目录不改变任何技能的运行时行为，仅作为离线审计工具。

## 目录结构

```
_token-audit/
├── scan_tokens.py        # 扫描脚本（纯 Python 标准库，无依赖）
├── token-budget.yaml     # 预算配置（各类文件字符数上限）
├── README.md             # 本文件
└── report.json           # 最近一次扫描报告（脚本自动生成）
```

## 快速开始

```powershell
# 扫描全部技能，输出控制台报告 + report.json
python .trae/skills/_token-audit/scan_tokens.py

# 只扫描单个技能
python .trae/skills/_token-audit/scan_tokens.py --skill wiki-code-dev

# 与基线报告对比（查看优化效果）
python .trae/skills/_token-audit/scan_tokens.py --compare .trae/skills/_token-audit/baseline_report.json

# 指定输出 JSON 路径
python .trae/skills/_token-audit/scan_tokens.py --json .trae/skills/_token-audit/my_report.json
```

## 预算规则

| 文件类别 | 字符数上限 | 说明 |
|---------|-----------|------|
| `skill_md` | 20000 | SKILL.md 入口文件，每次必读，最严格 |
| `config_file` | 35000 | config/ 目录下的配置文件 |
| `references_single` | 15000 | references/ 单文件（按需加载） |
| `defaults_yaml` | 15000 | defaults.yaml（只保留通用默认） |
| `skill_loader` | 20000 | skill-loader.md |
| `template_py` | 40000 | templates/*.py 模板脚本 |

| 技能 | 总 token 预算 |
|------|-------------|
| wiki-code-dev | 90000 |
| wiki-frontend-code-review | 80000 |
| wiki-backend-code-review | 90000 |
| wiki-auto-testing | 80000 |

四技能合计目标 ≤ 300K tokens。

## 冗余检测

脚本自动检测两类冗余信号：

1. **defaults/config 顶层 key 重合率 > 30%**：意味着 config.yaml 重复了 defaults.yaml 的内容，应精简为只保留项目覆盖项（config.yaml 第 4 行已声明"自动合并 defaults.yaml 的默认值"，是 deep merge 机制）。

2. **SKILL.md 章节 > 50 行**：建议拆分到 references/，SKILL.md 只保留入口导航 + 简述 + 链接（渐进式披露，一层引用深度）。

## 优化指引

当扫描报告出现超预算文件或冗余告警时，按以下优先级处理：

1. **SKILL.md 超预算**：将协议/复盘/历史等章节移到 references/，SKILL.md 保留意图、流程概览、配置表、导航链接。
2. **defaults/config 重合率高**：defaults.yaml 保留通用默认，config.yaml 只保留项目覆盖项 + 项目特定配置段。
3. **config 文件超预算**：压缩描述性文字，保留参数表，不删除任何参数项。
4. **references 单文件超预算**：按主题进一步拆分。

## 生成基线

优化前先运行一次扫描，将报告保存为基线：

```powershell
python .trae/skills/_token-audit/scan_tokens.py --json .trae/skills/_token-audit/baseline_report.json
```

优化后再运行对比，验证节省效果。
