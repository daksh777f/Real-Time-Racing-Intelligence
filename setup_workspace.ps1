<#
.SYNOPSIS
    Initialize the Race Analytics workspace structure and dependencies.

.DESCRIPTION
    Sets up the directory structure and Python environment for race analytics.
    
    This script:
    - Creates required directory structure
    - Sets up Python virtual environment
    - Installs dependencies from requirements.txt
    - Initializes data and output directories

.EXAMPLE
    .\setup_workspace.ps1

.NOTES
    Requires PowerShell 5.1+
    Requires Python 3.8+ installed
#>

param(
    [string]$SourcePath = "",
    [string]$TargetPath = $PSScriptRoot
)

Write-Host "Race Analytics - Workspace Setup" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Define directory structure
$directories = @(
    "data\raw\telemetry",
    "data\raw\results",
    "data\raw\sectors",
    "data\raw\weather",
    "data\raw\best_laps",
    "data\processed",
    "data\output",
    "src\race_engine\core",
    "src\race_engine\analysis",
    "src\race_engine\processing",
    "src\race_engine\sector_analysis",
    "src\race_engine\whatif",
    "src\race_engine\io",
    "src\race_engine\llm",
    "src\race_engine\utils",
    "scripts",
    "tests",
    ".github\workflows"
)

# Create directory structure
Write-Host "Creating directory structure..." -ForegroundColor Cyan
foreach ($dir in $directories) {
    $fullPath = Join-Path $TargetPath $dir
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  ✓ $dir" -ForegroundColor Green
    }
}

# Create Python package __init__.py files
Write-Host "`nInitializing Python packages..." -ForegroundColor Cyan
$packageDirs = @(
    "src\race_engine",
    "src\race_engine\core",
    "src\race_engine\analysis",
    "src\race_engine\processing",
    "src\race_engine\sector_analysis",
    "src\race_engine\whatif",
    "src\race_engine\io",
    "src\race_engine\llm",
    "src\race_engine\utils",
    "tests"
)

foreach ($pkg in $packageDirs) {
    $initPath = Join-Path $TargetPath "$pkg\__init__.py"
    if (-not (Test-Path $initPath)) {
        New-Item -ItemType File -Path $initPath -Force | Out-Null
        Write-Host "  ✓ $pkg" -ForegroundColor Green
    }
}

# Setup Python virtual environment
Write-Host "`nSetting up Python environment..." -ForegroundColor Cyan
$venvPath = Join-Path $TargetPath "venv"
$pythonPath = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPath)) {
    Write-Host "  Creating virtual environment..." -ForegroundColor Yellow
    python -m venv $venvPath
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
}

# Install dependencies
$requirementsPath = Join-Path $TargetPath "requirements.txt"
if (Test-Path $requirementsPath) {
    Write-Host "  Installing dependencies..." -ForegroundColor Yellow
    & $pythonPath -m pip install -q -r $requirementsPath 2>&1 | Out-Null
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
}

Write-Host "`n✅ Workspace setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Place your race data files in data/raw/ directories" -ForegroundColor White
Write-Host "  2. Run: .\venv\Scripts\activate" -ForegroundColor White
Write-Host "  3. Run: python examples_complete_workflow.py" -ForegroundColor White
Write-Host ""
