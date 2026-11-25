$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repo = Join-Path $projectRoot "mmaction2-main"
$python = Join-Path $projectRoot "runtime\python311\python.exe"

Push-Location $repo
try {
    & $python -X utf8 demo\webcam_demo.py `
        demo\demo_configs\tsn_r50_1x1x8_video_infer.py `
        checkpoints\tsn_r50_kinetics400.pth `
        tools\data\kinetics\label_map_k400.txt `
        --device cuda:0 `
        --camera-id 0 `
        --threshold 0.1 `
        --average-size 2 `
        --drawing-fps 10 `
        --inference-fps 2
} finally {
    Pop-Location
}

if ($LASTEXITCODE -ne 0) {
    throw "Webcam demo failed with exit code $LASTEXITCODE"
}
