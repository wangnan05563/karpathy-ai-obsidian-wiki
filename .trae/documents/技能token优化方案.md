# 技能 Token 优化方案

## Context（背景）

四个核心 wiki-* 技能合计约 **500K tokens**，每次加载技能时消耗大量上下文：

| 技能 | 文件数 | 字符数 | 近似 token |
|------|--------|--------|-----------|
| wiki-backend-code-review | 54 | 453K | ~130K |
| wiki-code-dev | 75 | 448K | ~128K |
| wiki-auto-testing | 18 | 443K | ~127K |
| wiki-frontend-code-review | 53 | 400K | ~114K |

**核心痛点**（基于扫描数据）：
1. **入口文件过大**：wiki-auto-testing/SKILL.md 达 68K 字符（~19.5K tokens），每次必读
2. **defaults/config 重复**：wiki-auto-testing 的 defaults.yaml（39K）与 config.yaml（67K）重复度 ~80%
3. **config 描述冗余**：各 config 文件 50-64K 字符，含大量可压缩的描述性文字
4. **大文件未拆分**：SKILL.md 内含协议/复盘/历史等章节，未按渐进式披露拆到 references
5. **缺乏监控**：无 token 预算机制，无法防止文件再次膨胀

**目标**：在不丢失任何规则语义、不影响审查/测试能力的前提下，将四个技能总 token 降至 ~300K（节省 ~40%），并建立长期监控机制防止回涨。

**用户确认的方向**：
- 范围：仅 wiki-* 四个技能文件本身
- 策略：中间（去冗余 + 拆分大文件 + 建预算机制）
- 监控形态：独立扫描脚本 + 预算配置文件

---

## 实施方案

### 阶段 1：建立 Token 监控机制（零风险，先建基础）

新建 `.trae/skills/_token-audit/` 目录，含三个文件：

#### 1.1 `scan_tokens.py`（扫描脚本）
功能：
- 扫描 `.trae/skills/` 下所有技能的 `.md/.yaml/.yml/.py` 文件
- 统计每个技能、每个文件的字符数/行数/近似 token（chars/3.5）
- 读取 `token-budget.yaml` 预算配置，标记超预算文件
- 识别冗余信号：defaults/config 重复度、SKILL.md 中可移走的章节（>50 行的复盘/协议/历史章节）
- 输出报告：控制台表格 + `_token-audit/report.json`（供后续对比）

技术要点：
- 纯 Python 标准库（无依赖，跨平台）
- UTF-8 读取，兼容中文
- 支持 `--skill <name>` 单技能扫描、`--compare <old_report>` 对比模式
- 重复度检测：对比 defaults.yaml 与 config.yaml 的顶层 key 重合率

#### 1.2 `token-budget.yaml`（预算配置）
```yaml
# 各类文件的 token 上限（字符数，token ≈ 字符数/3.5）
budgets:
  skill_md: 20000        # SKILL.md 入口文件（每次必读，最严格）
  config_file: 35000     # config 目录下的配置文件
  references_single: 15000  # references/ 单文件
  defaults_yaml: 15000   # defaults.yaml（只保留通用默认）
  skill_loader: 20000    # skill-loader.md
  template_py: 40000     # templates/*.py 模板脚本

# 各技能总 token 预算
skill_total_budgets:
  wiki-code-dev: 90000
  wiki-frontend-code-review: 80000
  wiki-backend-code-review: 90000
  wiki-auto-testing: 80000

# 冗余阈值
redundancy_thresholds:
  defaults_config_overlap_pct: 30  # defaults/config 顶层 key 重合率超 30% 告警
  skill_md_movable_section_lines: 50  # SKILL.md 中 >50 行的章节建议拆分
```

#### 1.3 `README.md`（使用说明）
含运行方式、预算规则、优化指引。

---

### 阶段 2：wiki-auto-testing 优化（ROI 最高）

#### 2.1 SKILL.md 拆分（68K → 目标 ≤ 20K）

将以下章节移到 references/，SKILL.md 只保留入口导航 + 简述 + 链接：

| 待移走章节 | 行数范围 | 目标文件 |
|-----------|---------|---------|
| 前置检查协议 / 测试用例同步协议 / 失败分类协议 / 服务管理协议 / 搜索交叉验证协议 | L1017-1330（~310 行） | `references/protocols.md`（新建，合并） |
| 文件夹上传批量编译测试复盘 | L1343-1430（~90 行） | `references/batch-compile-testing.md`（新建） |
| Tauri 2.x 桌面应用测试（复盘提炼） | L1448-1619（~170 行） | 合并到已有 `references/tauri-desktop-testing.md` |
| v3 媒体生成工具测试（复盘提炼） | L717-847（~130 行） | `references/media-generation-testing.md`（新建） |
| 持久化层 / Async 可靠性 / 配置一致性 / 目录结构验证（各复盘提炼） | L420-716（~300 行） | `references/testing-patterns.md`（新建，合并） |
| Version History | L1331-1342 | 压缩为最近 3 版（v2.2.0/v2.1.0/v2.0.0），旧版移到 `references/changelog.md`（新建） |

SKILL.md 保留：技能意图、配置文件表、6 阶段流程概览、核心配置块表、动态引擎步骤类型表、破坏性按钮保护机制、适配新项目、适用/不适用场景、故障排查引用、版本历史（最近 3 版）。

#### 2.2 defaults.yaml / config.yaml 去重（107K → 目标 ~45K）

**机制已确认**：config.yaml 第 4 行"自动合并 defaults.yaml 的默认值"——deep merge，config.yaml 可安全精简。

策略：
- **defaults.yaml**：保留所有配置段的"通用默认值"（项目无关），删除项目特定值。目标 ≤ 15K。
- **config.yaml**：只保留项目覆盖项（与 defaults 不同的值）+ 项目特定配置段（如 navigation.pages、api_tests.endpoints）。目标 ≤ 30K。
- 对每个配置段判断：值与通用默认一致 → 从 config.yaml 删除；项目特定 → 保留在 config.yaml。

预计去重率 55%+，从 107K 降至 ~45K。

---

### 阶段 3：wiki-code-dev 优化

#### 3.1 SKILL.md 精简（39K → 目标 ≤ 20K）

| 待移走章节 | 行数范围 | 目标文件 |
|-----------|---------|---------|
| 完整文档结构 | L324-409（~86 行） | `references/document-structure.md`（新建） |
| 必检清单（详细版） | L200-278（~79 行） | 精简为概要表，详情移到 `references/checklist-details.md`（新建） |
| 项目背景速查 | L294-323（~30 行） | 移到 `config/coding-standards-config.md` 顶部 |
| Version History | L509-526 | 压缩为最近 3 版，旧版移到 `references/changelog.md`（新建） |

#### 3.2 coding-standards-config.md 精简（64K → 目标 ≤ 35K）

策略：压缩每个参数段的描述性文字（保留参数表，删除冗余说明段落），合并相似参数段。不删除任何参数项。

---

### 阶段 4：wiki-backend-code-review 优化

#### 4.1 SKILL.md 精简（40K → 目标 ≤ 20K）

| 待移走章节 | 目标 |
|-----------|---------|
| Historical Incident Coverage 表格 | 移到 `references/historical-incidents.md`（新建） |
| Version History | 压缩为最近 3 版 |
| 详细审查步骤 | 概要留在 SKILL.md，详情已在 references |

#### 4.2 review-config.md 精简（63K → 目标 ≤ 35K）

压缩描述性文字，保留参数表。

#### 4.3 skill-loader.md 与 SKILL.md 去重

检查 skill-loader.md（30K）与 SKILL.md 的重复内容，skill-loader.md 只保留规则路由表，不重复 SKILL.md 的意图/流程。

---

### 阶段 5：wiki-frontend-code-review 优化（轻度）

已较精简（SKILL.md 27K），仅做：
- review-config.md（49K）压缩描述 → 目标 ≤ 35K
- skill-loader.md（30K）与 SKILL.md 去重
- Version History 压缩为最近 3 版

---

### 阶段 6：验证

#### 6.1 Token 扫描验证
```powershell
python .trae/skills/_token-audit/scan_tokens.py --compare .trae/skills/_token-audit/baseline_report.json
```
对比优化前后总 token，确认达到 ~300K 目标。

#### 6.2 语法验证
- YAML：`python -c "import yaml; yaml.safe_load(open(f))"` 验证所有 .yaml 文件
- 链接：扫描所有 markdown 相对链接，验证目标文件存在

#### 6.3 规则语义完整性验证
- 对比优化前后各技能的规则编号（BR/FR/CODING）清单，确认无规则丢失
- 验证 skill-loader.md 的规则路由表覆盖所有 references 文件

#### 6.4 编码验证
- 所有修改文件 UTF-8 无 BOM

---

## 预期收益

| 指标 | 优化前 | 优化后（目标） | 节省 |
|------|--------|--------------|------|
| 四技能总 token | ~500K | ~300K | ~40% |
| wiki-auto-testing SKILL.md | 19.5K | ~6K | ~69% |
| wiki-auto-testing defaults+config | 30K | ~13K | ~57% |
| wiki-code-dev SKILL.md | 11K | ~6K | ~45% |
| wiki-code-dev config | 18.4K | ~10K | ~46% |
| 监控机制 | 无 | 扫描脚本+预算 | 防回涨 |

## 风险与回滚

- **风险**：拆分 SKILL.md 可能导致技能加载时遗漏 references 内容
- **缓解**：SKILL.md 保留清晰的"Loading Sequence"导航，明确何时加载哪个 references；渐进式披露一层引用深度
- **回滚条件**：若优化后技能执行出现规则遗漏（如审查未命中已知规则），回滚对应文件的拆分
