# 项目类型自动检测脚本
# 用途：检测项目根目录下的文件特征，自动识别项目类型（Python/TypeScript/Java/Go/Multi-language），
#       生成 project_config.json 草稿，支持交互式确认和手动调整
# 入口：.\scripts\detect-project.ps1 -Path "." [-OutputPath ".\config\project_config.json"] [-NonInteractive]
# 输出：
#   1. 控制台输出检测结果（项目类型、识别到的文件、生成的模块结构）
#   2. 生成 project_config.json 草稿文件（默认写入 config/project_config.json，已存在则备份为 .bak）
#
# 设计原则：
#   - 配置驱动：检测规则从内置默认表读取，可扩展为从 config/detect_rules.json 加载
#   - 通用泛化：支持 Python/TypeScript/Java/Go 四大语言，自动识别常见框架
#   - 非破坏性：已存在的 project_config.json 会备份为 .bak，不直接覆盖
#   - 可交互：默认交互式确认，-NonInteractive 用于自动化场景

[CmdletBinding()]
param(
    [string]$Path = ".",
    [string]$OutputPath = "",
    [switch]$NonInteractive
)

# 兜底处理：$PSScriptRoot 在某些调用方式下可能为空，
# 此时回退到脚本文件自身的目录，确保默认输出路径始终可解析
if (-not $OutputPath) {
    $scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    if (-not $scriptDir) { $scriptDir = "." }
    $OutputPath = Join-Path $scriptDir "..\config\project_config.json"
}

# 项目类型检测规则表（按文件特征识别）
# 每条规则包含：marker_files（标记文件）、language（语言）、frameworks（候选框架）、exclude（默认排除）
$Script:DetectRules = @(
    # Python 项目
    @{
        Name = "python"
        MarkerFiles = @("requirements.txt", "pyproject.toml", "setup.py", "Pipfile", "poetry.lock")
        Languages = @("python")
        CandidateFrameworks = @(
            @{ Marker = "fastapi"; Files = @("requirements.txt", "pyproject.toml"); Pattern = "fastapi" },
            @{ Marker = "django"; Files = @("requirements.txt", "pyproject.toml"); Pattern = "django" },
            @{ Marker = "flask"; Files = @("requirements.txt", "pyproject.toml"); Pattern = "flask" }
        )
        DefaultSrcPath = "src"
        DefaultExclude = @("__pycache__", "*.pyc", ".git", "dist", "build", "tests", "venv", ".venv")
        DefaultTestCommand = "pytest tests/"
    },
    # TypeScript/JavaScript 项目
    @{
        Name = "typescript"
        MarkerFiles = @("package.json", "tsconfig.json")
        Languages = @("typescript")
        CandidateFrameworks = @(
            @{ Marker = "react"; Files = @("package.json"); Pattern = '"react"' },
            @{ Marker = "vue"; Files = @("package.json"); Pattern = '"vue"' },
            @{ Marker = "express"; Files = @("package.json"); Pattern = '"express"' },
            @{ Marker = "nest"; Files = @("package.json"); Pattern = '"@nestjs' }
        )
        DefaultSrcPath = "src"
        DefaultExclude = @("node_modules", "dist", "build", ".git", "coverage", "*.test.ts", "*.spec.ts")
        DefaultTestCommand = "npm test"
    },
    # Java 项目
    @{
        Name = "java"
        MarkerFiles = @("pom.xml", "build.gradle", "build.gradle.kts")
        Languages = @("java")
        CandidateFrameworks = @(
            @{ Marker = "spring"; Files = @("pom.xml", "build.gradle", "build.gradle.kts"); Pattern = "spring" }
        )
        DefaultSrcPath = "src/main/java"
        DefaultExclude = @("target", ".git", "build", "*.class")
        DefaultTestCommand = "mvn test"
    },
    # Go 项目
    @{
        Name = "go"
        MarkerFiles = @("go.mod")
        Languages = @("go")
        CandidateFrameworks = @()
        DefaultSrcPath = "."
        DefaultExclude = @("vendor", ".git", "bin")
        DefaultTestCommand = "go test ./..."
    }
)

# 项目类型识别函数
# 返回：识别到的项目类型数组（支持多语言项目）
function Detect-ProjectType {
    param([string]$ProjectPath)

    $detectedTypes = @()

    foreach ($rule in $Script:DetectRules) {
        $markerFound = $false
        foreach ($marker in $rule.MarkerFiles) {
            $markerPath = Join-Path $ProjectPath $marker
            if (Test-Path $markerPath) {
                $markerFound = $true
                break
            }
        }
        if ($markerFound) {
            $detectedTypes += $rule
        }
    }

    return $detectedTypes
}

# 框架识别函数
# 读取标记文件内容，按候选框架的 Pattern 匹配
function Detect-Frameworks {
    param($Rule, [string]$ProjectPath)

    $frameworks = @()
    foreach ($candidate in $rule.CandidateFrameworks) {
        foreach ($file in $candidate.Files) {
            $filePath = Join-Path $ProjectPath $file
            if (Test-Path $filePath) {
                $content = Get-Content $filePath -Raw -ErrorAction SilentlyContinue
                if ($content -and $content -match $candidate.Pattern) {
                    $frameworks += $candidate.Marker
                    break
                }
            }
        }
    }
    return $frameworks
}

# 生成 project_config.json 草稿
function New-ProjectConfigDraft {
    param($DetectedTypes, [string]$ProjectPath)

    $projectKey = Split-Path $ProjectPath -Leaf
    if (-not $projectKey) { $projectKey = "my_project" }
    # 规范化项目 key：小写、下划线分隔
    $projectKey = $projectKey -replace '[^a-zA-Z0-9_]', '_'
    $projectKey = $projectKey.ToLower()

    $modules = @{}
    $testCommands = @{}

    foreach ($rule in $DetectedTypes) {
        $moduleName = if ($DetectedTypes.Count -eq 1) { "backend" } else { $rule.Name }
        $frameworks = Detect-Frameworks -Rule $rule -ProjectPath $ProjectPath

        $modules[$moduleName] = @{
            path = $rule.DefaultSrcPath
            languages = $rule.Languages
            frameworks = $frameworks
            exclude = $rule.DefaultExclude
        }
        $testCommands[$moduleName] = $rule.DefaultTestCommand
    }

    $config = @{
        _meta = @{
            file = "project_config.json"
            purpose = "由 detect-project.ps1 自动生成的项目配置草稿，请根据实际情况调整"
            version = "2.3.0"
            schema_version = "2.3.0"
            last_updated = (Get-Date -Format "yyyy-MM-dd")
            auto_generated = $true
        }
        project = @{
            key = $projectKey
            name = $projectKey
            base_path = "."
            description = "Auto-generated by detect-project.ps1"
        }
        business_constraints = @{
            _description = "业务特定硬约束文件加载清单（空数组表示仅加载 core.json 通用规则）"
            load_files = @()
        }
        modules = $modules
        verify = @{
            test_command = ($testCommands.Values | Select-Object -First 1)
            test_commands = $testCommands
        }
        report = @{
            output_dir = "docs/sonar-reports/"
        }
        fix_strategies_overrides = @{
            _description = "项目级修复策略覆盖（与 config/fix_strategies.json 配合使用）"
            rule_overrides = @{}
        }
    }

    return $config
}

# 主流程
$Script:ProjectPath = (Resolve-Path $Path).Path
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SonarQube MCP - 项目类型自动检测" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "项目路径: $Script:ProjectPath"
Write-Host ""

# Step 1: 检测项目类型
$detectedTypes = Detect-ProjectType -ProjectPath $Script:ProjectPath

if ($detectedTypes.Count -eq 0) {
    Write-Host "[ERROR] 未识别到任何项目类型（Python/TypeScript/Java/Go）" -ForegroundColor Red
    Write-Host "请在项目根目录确保存在以下文件之一："
    foreach ($rule in $Script:DetectRules) {
        Write-Host "  - $($rule.Name): $($rule.MarkerFiles -join ', ')"
    }
    exit 1
}

Write-Host "[1/3] 识别到项目类型：" -ForegroundColor Green
foreach ($rule in $detectedTypes) {
    $frameworks = Detect-Frameworks -Rule $rule -ProjectPath $Script:ProjectPath
    $frameworksStr = if ($frameworks.Count -gt 0) { "（框架: $($frameworks -join ', ')）" } else { "（无框架）" }
    Write-Host "  - $($rule.Name)$frameworksStr"
}
Write-Host ""

# Step 2: 交互式确认（非 -NonInteractive 模式）
if (-not $NonInteractive) {
    Write-Host "[2/3] 即将生成 project_config.json 草稿" -ForegroundColor Yellow
    $confirmation = Read-Host "确认继续？(Y/N)"
    if ($confirmation -ne "Y" -and $confirmation -ne "y") {
        Write-Host "用户取消操作" -ForegroundColor Yellow
        exit 0
    }
}

# Step 3: 生成配置文件
Write-Host "[3/3] 生成 project_config.json..." -ForegroundColor Green

$configDraft = New-ProjectConfigDraft -DetectedTypes $detectedTypes -ProjectPath $Script:ProjectPath

# 备份已存在的配置文件
if (Test-Path $OutputPath) {
    $backupPath = "$OutputPath.bak"
    Copy-Item -Path $OutputPath -Destination $backupPath -Force
    Write-Host "  已备份原配置文件到: $backupPath" -ForegroundColor Yellow
}

# 确保输出目录存在
$outputDir = Split-Path $OutputPath -Parent
if (-not (Test-Path $outputDir)) {
    New-Item -Path $outputDir -ItemType Directory -Force | Out-Null
}

# 写入配置文件（UTF-8 无 BOM）
$jsonContent = $configDraft | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText($OutputPath, $jsonContent, [System.Text.UTF8Encoding]::new($false))

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  生成成功" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  输出文件: $OutputPath"
Write-Host "  项目 Key: $($configDraft.project.key)"
Write-Host "  模块数量: $($configDraft.modules.Count)"
Write-Host ""
Write-Host "下一步：" -ForegroundColor Cyan
Write-Host "  1. 检查并调整 $OutputPath 中的模块路径和测试命令"
Write-Host "  2. 设置环境变量（见 SKILL.md '配置环境变量' 章节）"
Write-Host "  3. 运行 .\scripts\validate-config.ps1 校验配置完整性"
Write-Host "  4. 运行 .\scripts\verify-connection.ps1 验证连接"
Write-Host "  5. 运行 .\scripts\run-sonar-scanner.ps1 执行扫描"
