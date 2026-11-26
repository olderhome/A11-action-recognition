param(
    [switch]$CpuOnly,
    [switch]$SkipWeights
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvRoot = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"

function Find-BootstrapPython {
    $candidates = @(
        @{ Command = "py"; Args = @("-3.11") },
        @{ Command = "py"; Args = @("-3.10") },
        @{ Command = "python"; Args = @() }
    )
    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate.Command -ErrorAction SilentlyContinue
        if (-not $command) {
            continue
        }
        & $command.Source @($candidate.Args) -c `
            "import sys; raise SystemExit(0 if (3,10) <= sys.version_info[:2] <= (3,11) else 1)"
        if ($LASTEXITCODE -eq 0) {
            return $candidate
        }
    }
    throw "Python 3.10 or 3.11 is required. Install it, then run setup.ps1 again."
}

if (-not (Test-Path -LiteralPath $venvPython)) {
    $bootstrap = Find-BootstrapPython
    Write-Host "Creating .venv with Python 3.10/3.11..."
    & $bootstrap.Command @($bootstrap.Args) -m venv $venvRoot
}

& $venvPython -m pip install --upgrade pip setuptools wheel

if ($CpuOnly) {
    Write-Host "Installing CPU PyTorch..."
    & $venvPython -m pip install `
        torch==2.0.1+cpu torchvision==0.15.2+cpu `
        --index-url https://download.pytorch.org/whl/cpu
    & $venvPython -m pip install `
        -r (Join-Path $projectRoot "requirements-common.txt")
} else {
    Write-Host "Installing CUDA 11.8 PyTorch and experiment dependencies..."
    & $venvPython -m pip install `
        -r (Join-Path $projectRoot "requirements.txt")
}

Write-Host "Installing MMAction2..."
& $venvPython -m pip install `
    -e (Join-Path $projectRoot "mmaction2-main") --no-deps

if (-not $SkipWeights) {
    Write-Host "Downloading demonstration weights..."
    & powershell -ExecutionPolicy Bypass `
        -File (Join-Path $projectRoot "download_model_weights.ps1")
}

& $venvPython -X utf8 -m a11code.collect_environment

Write-Host ""
Write-Host "Setup complete."
Write-Host "Dashboard: powershell -ExecutionPolicy Bypass -File .\run_comparison_app.ps1"
Write-Host "Webcam:    powershell -ExecutionPolicy Bypass -File .\run_webcam.ps1"
