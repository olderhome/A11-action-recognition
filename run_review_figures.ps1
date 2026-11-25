param(
    [string]$ExperimentDir = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot "runtime\python311\python.exe"
$generator = Join-Path $projectRoot "mmaction2-main\a11_tools\generate_paper_figures.py"

if (-not $ExperimentDir) {
    $latest = Get-ChildItem -Directory -LiteralPath `
        (Join-Path $projectRoot "outputs\experiments") |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $latest) {
        throw "No experiment directory found."
    }
    $ExperimentDir = $latest.FullName
}

$reviewDir = Join-Path $projectRoot (
    "outputs\review_" + (Get-Date -Format "yyyyMMdd")
)
$figureDir = Join-Path $reviewDir "figures"

& $python -X utf8 $generator `
    --experiment-dir $ExperimentDir `
    --output-dir $figureDir

if ($LASTEXITCODE -ne 0) {
    throw "Figure generation failed with exit code $LASTEXITCODE"
}

Write-Host "Figures: $figureDir"
