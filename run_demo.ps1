param(
    [string]$Device = "auto"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Join-Path $projectRoot "mmaction2-main"
. (Join-Path $projectRoot "a11_env.ps1")
$python = Resolve-A11Python -ProjectRoot $projectRoot
if ($Device -eq "auto") {
    $Device = (& $python -c "import torch; print('cuda:0' if torch.cuda.is_available() else 'cpu')").Trim()
}
$outputDir = Join-Path $projectRoot "outputs"
$outputFile = Join-Path $outputDir "demo_tsn.mp4"

New-Item -ItemType Directory -Force -Path $outputDir | Out-Null

Push-Location $repo
try {
    & $python -X utf8 demo\demo.py `
        demo\demo_configs\tsn_r50_1x1x8_video_infer.py `
        checkpoints\tsn_r50_kinetics400.pth `
        demo\demo.mp4 `
        tools\data\kinetics\label_map_k400.txt `
        --device $Device `
        --out-filename $outputFile
} finally {
    Pop-Location
}

if ($LASTEXITCODE -ne 0) {
    throw "Demo inference failed with exit code $LASTEXITCODE"
}

Write-Host "Output video: $outputFile"
