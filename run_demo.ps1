$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Join-Path $projectRoot "mmaction2-main"
$python = Join-Path $projectRoot "runtime\python311\python.exe"
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
        --device cuda:0 `
        --out-filename $outputFile
} finally {
    Pop-Location
}

if ($LASTEXITCODE -ne 0) {
    throw "Demo inference failed with exit code $LASTEXITCODE"
}

Write-Host "Output video: $outputFile"
