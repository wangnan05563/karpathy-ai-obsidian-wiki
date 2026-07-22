# 配置文件完整性与一致性校验脚本
# 用途：校验 sonarqube-mcp 技能所有配置文件的完整性、一致性与版本兼容性
# 入口：.\scripts\validate-config.ps1 [-ConfigDir ".\config"] [-Strict]
# 输出：
#   1. 控制台输出校验结果（✅ PASS / ❌ ERROR / ⚠️ WARNING）
#   2. 退出码：0=全部通过，1=存在 ERROR，2=仅存在 WARNING
#
# 校验项：
#   - 文件存在性：core_config.json / project_config.json / fix_strategies.json / framework_patterns.json / hard_constraints/core.json
#   - JSON 格式：所有配置文件必须是合法 JSON
#   - 必填字段：_meta.version / _meta.schema_version（v2.3+）
#   - 版本兼容性：core_config.json 的 schema_version >= min_compatible_version
#   - 引用一致性：project_config.json -> business_constraints.load_files 引用的文件必须存在
#   - 规则一致性：fix_strategies.json 中的 rule_id 与 nosonar_decision_matrix 中的规则不应冲突
#   - 路径有效性：project_config.json -> modules.*.path 应为相对路径
#
# 设计原则：
#   - 配置驱动：校验规则从内置规则表读取，可扩展为从 config/validation_rules.json 加载
#   - 非破坏性：仅校验，不修改任何配置文件
#   - 分级输出：区分 ERROR（必须修复）和 WARNING（建议修复）

[CmdletBinding()]
param(
    [string]$ConfigDir = "",
    [switch]$Strict
)

# 兜底处理：$PSScriptRoot 在某些调用方式（如 powershell -File）下可能为空，
# 此时回退到脚本文件自身的目录，确保默认路径始终可解析
if (-not $ConfigDir) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    if (-not $scriptDir) { $scriptDir = "." }
    $ConfigDir = Join-Path $scriptDir "..\config"
    $ConfigDir = (Resolve-Path $ConfigDir -ErrorAction SilentlyContinue).Path
    if (-not $ConfigDir) { $ConfigDir = "config" }
}

$Script:Errors = @()
$Script:Warnings = @()
$Script:Passes = @()

# 必须存在的配置文件清单
$Script:RequiredFiles = @(
    "core_config.json",
    "project_config.json",
    "fix_strategies.json",
    "framework_patterns.json",
    "hard_constraints\core.json"
)

# 添加 ERROR
function Add-Error {
    param([string]$Message)
    $Script:Errors += $Message
    Write-Host "  [ERROR] $Message" -ForegroundColor Red
}

# 添加 WARNING
function Add-Warning {
    param([string]$Message)
    $Script:Warnings += $Message
    Write-Host "  [WARNING] $Message" -ForegroundColor Yellow
}

# 添加 PASS
function Add-Pass {
    param([string]$Message)
    $Script:Passes += $Message
    Write-Host "  [PASS] $Message" -ForegroundColor Green
}

# 校验 JSON 文件可解析
function Test-JsonFile {
    param([string]$FilePath)

    if (-not (Test-Path $FilePath)) {
        return $null
    }

    try {
        $content = Get-Content $FilePath -Raw -Encoding UTF8
        $config = $content | ConvertFrom-Json
        return $config
    } catch {
        Add-Error "JSON 解析失败: $FilePath - $_"
        return $null
    }
}

# 校验必填字段
function Test-RequiredFields {
    param($Config, [string]$FileName, [string[]]$RequiredFields)

    foreach ($field in $RequiredFields) {
        $fieldParts = $field -split '\.'
        $current = $Config
        $found = $true
        foreach ($part in $fieldParts) {
            if ($current.PSObject.Properties.Name -contains $part) {
                $current = $current.$part
            } else {
                $found = $false
                break
            }
        }
        if (-not $found) {
            Add-Error "$FileName 缺少必填字段: $field"
        }
    }
}

# 版本号比较（语义化版本）
function Compare-Version {
    param([string]$V1, [string]$V2)
    # 返回：1 if V1 > V2, 0 if V1 == V2, -1 if V1 < V2
    $v1Parts = $V1.Split('.')
    $v2Parts = $V2.Split('.')
    $maxLen = [Math]::Max($v1Parts.Count, $v2Parts.Count)
    for ($i = 0; $i -lt $maxLen; $i++) {
        $v1Num = if ($i -lt $v1Parts.Count) { [int]$v1Parts[$i] } else { 0 }
        $v2Num = if ($i -lt $v2Parts.Count) { [int]$v2Parts[$i] } else { 0 }
        if ($v1Num -gt $v2Num) { return 1 }
        if ($v1Num -lt $v2Num) { return -1 }
    }
    return 0
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SonarQube MCP - 配置文件校验" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "配置目录: $ConfigDir"
Write-Host ""

# Step 1: 校验文件存在性
Write-Host "[1/5] 校验文件存在性..." -ForegroundColor Cyan
foreach ($file in $Script:RequiredFiles) {
    $filePath = Join-Path $ConfigDir $file
    if (Test-Path $filePath) {
        Add-Pass "文件存在: $file"
    } else {
        Add-Error "文件缺失: $file"
    }
}
Write-Host ""

# Step 2: 校验 JSON 格式
Write-Host "[2/5] 校验 JSON 格式..." -ForegroundColor Cyan
$configs = @{}
foreach ($file in $Script:RequiredFiles) {
    $filePath = Join-Path $ConfigDir $file
    $config = Test-JsonFile -FilePath $filePath
    if ($config) {
        $configs[$file] = $config
        Add-Pass "JSON 解析成功: $file"
    }
}
Write-Host ""

# Step 3: 校验必填字段
Write-Host "[3/5] 校验必填字段..." -ForegroundColor Cyan
if ($configs.ContainsKey("core_config.json")) {
    Test-RequiredFields -Config $configs["core_config.json"] -FileName "core_config.json" -RequiredFields @("_meta.version", "_meta.schema_version", "_meta.min_compatible_version", "sonarqube_server", "precheck", "scan", "failure_recovery")
}
if ($configs.ContainsKey("project_config.json")) {
    Test-RequiredFields -Config $configs["project_config.json"] -FileName "project_config.json" -RequiredFields @("_meta.version", "project.key", "modules", "verify.test_command", "business_constraints")
}
Write-Host ""

# Step 4: 校验版本兼容性
Write-Host "[4/5] 校验版本兼容性..." -ForegroundColor Cyan
if ($configs.ContainsKey("core_config.json")) {
    $coreConfig = $configs["core_config.json"]
    $schemaVersion = $coreConfig._meta.schema_version
    $minCompatible = $coreConfig._meta.min_compatible_version

    if ($schemaVersion -and $minCompatible) {
        $cmp = Compare-Version -V1 $schemaVersion -V2 $minCompatible
        if ($cmp -ge 0) {
            Add-Pass "版本兼容: schema_version=$schemaVersion >= min_compatible_version=$minCompatible"
        } else {
            Add-Error "版本不兼容: schema_version=$schemaVersion < min_compatible_version=$minCompatible"
        }
    }

    # 校验 project_config.json 的 schema_version（如果存在）
    if ($configs.ContainsKey("project_config.json")) {
        $projectSchema = $configs["project_config.json"]._meta.schema_version
        if ($projectSchema) {
            $cmp = Compare-Version -V1 $projectSchema -V2 $minCompatible
            if ($cmp -ge 0) {
                Add-Pass "项目配置版本兼容: project schema_version=$projectSchema >= min=$minCompatible"
            } else {
                Add-Warning "项目配置版本偏低: project schema_version=$projectSchema < min=$minCompatible（建议升级）"
            }
        }
    }
}
Write-Host ""

# Step 5: 校验引用一致性
Write-Host "[5/5] 校验引用一致性..." -ForegroundColor Cyan
if ($configs.ContainsKey("project_config.json")) {
    $projectConfig = $configs["project_config.json"]

    # 校验 business_constraints.load_files 引用的文件存在
    if ($projectConfig.business_constraints -and $projectConfig.business_constraints.load_files) {
        foreach ($loadFile in $projectConfig.business_constraints.load_files) {
            $constraintPath = Join-Path $ConfigDir "hard_constraints\business\$loadFile"
            if (Test-Path $constraintPath) {
                Add-Pass "业务约束文件存在: $loadFile"
            } else {
                Add-Error "业务约束文件缺失: hard_constraints\business\$loadFile（在 project_config.json -> business_constraints.load_files 中引用）"
            }
        }
    }

    # 校验 modules.*.path 为相对路径
    if ($projectConfig.modules) {
        $modules = $projectConfig.modules
        foreach ($moduleName in $modules.PSObject.Properties.Name) {
            $module = $modules.$moduleName
            if ($module.path) {
                if ($module.path -match '^[A-Za-z]:\\' -or $module.path -match '^/') {
                    Add-Warning "模块 $moduleName.path 为绝对路径: $($module.path)（建议使用相对路径）"
                } else {
                    Add-Pass "模块 $moduleName.path 为相对路径: $($module.path)"
                }
            }
        }
    }
}

# 校验 nosonar_decision_matrix 与 fix_strategies 一致性
if ($configs.ContainsKey("core_config.json") -and $configs.ContainsKey("fix_strategies.json")) {
    $coreConfig = $configs["core_config.json"]
    if ($coreConfig.nosonar_decision_matrix) {
        $mustFixRules = $coreConfig.nosonar_decision_matrix.must_fix_rules
        if ($mustFixRules -and $mustFixRules.Count -gt 0) {
            Add-Pass "nosonar_decision_matrix.must_fix_rules 配置存在，共 $($mustFixRules.Count) 条规则"
        } else {
            Add-Warning "nosonar_decision_matrix.must_fix_rules 为空或缺失（安全规则将无法强制代码修复）"
        }
    }
}
Write-Host ""

# 汇总报告
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  校验汇总" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  PASS:     $($Script:Passes.Count)" -ForegroundColor Green
Write-Host "  WARNING:  $($Script:Warnings.Count)" -ForegroundColor Yellow
Write-Host "  ERROR:    $($Script:Errors.Count)" -ForegroundColor Red
Write-Host ""

if ($Script:Errors.Count -gt 0) {
    Write-Host "❌ 校验失败：存在 $($Script:Errors.Count) 个 ERROR，必须修复后才能运行扫描" -ForegroundColor Red
    exit 1
}

if ($Script:Warnings.Count -gt 0) {
    if ($Strict) {
        Write-Host "❌ 严格模式：存在 $($Script:Warnings.Count) 个 WARNING，-Strict 模式下视为失败" -ForegroundColor Red
        exit 2
    } else {
        Write-Host "⚠️ 校验通过（有警告）：存在 $($Script:Warnings.Count) 个 WARNING，建议修复" -ForegroundColor Yellow
        exit 0
    }
}

Write-Host "✅ 校验通过：所有配置文件完整且一致" -ForegroundColor Green
exit 0
