param(
    [switch]$SkipDataPreparation
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot "runtime\python311\python.exe"
$videoRoot = Join-Path $projectRoot "mmaction2-main\data\ucf101\videos"

if (-not $SkipDataPreparation -and -not (Test-Path -LiteralPath $videoRoot)) {
    & (Join-Path $projectRoot "prepare_ucf101.ps1")
}

Push-Location $projectRoot
try {
    & $python -X utf8 -m a11code.build_manifest

    $memoryOutput = (& $python -X utf8 -m a11code.run_memory_matrix)
    $memoryOutput
    $memoryDirLine = $memoryOutput |
        Where-Object { $_ -like 'Memory matrix:*' } |
        Select-Object -Last 1
    $memoryDir = $memoryDirLine.Substring(
        'Memory matrix:'.Length).Trim()

    $pipelineOutput = (& $python -X utf8 -m a11code.run_feature_pipeline `
        --suite all)
    $pipelineOutput
    $matrixLine = $pipelineOutput |
        Where-Object { $_ -like 'Experiment matrix:*' } |
        Select-Object -Last 1
    $pipelineDir = $matrixLine.Substring(
        'Experiment matrix:'.Length).Trim()
    $matrixPath = Join-Path $pipelineDir "matrix.json"

    & $python -X utf8 -m a11code.summarize_results `
        --matrix $matrixPath `
        --output-dir (Join-Path $pipelineDir "summary")
    & $python -X utf8 -m a11code.plot_feature_results `
        --matrix $matrixPath `
        --output-dir (Join-Path $projectRoot "figures")
    & $python -X utf8 -m a11code.plot_dataset `
        --output-dir (Join-Path $projectRoot "figures")
    & $python -X utf8 -m a11code.plot_memory_results `
        --matrix (Join-Path $memoryDir "matrix.json") `
        --output-dir (Join-Path $projectRoot "figures")

    $matrix = Get-Content -Raw -LiteralPath $matrixPath |
        ConvertFrom-Json
    $chosen = $matrix |
        Where-Object {
            $_.suite -eq "main" -and
            $_.config -eq "tsn2d_uniform" -and
            $_.probe_type -eq "temporal" -and
            $_.seed -eq 0
        } |
        Select-Object -First 1
    if ($chosen) {
        $predictions = Join-Path (
            Split-Path -Parent $chosen.metrics_path) "predictions.csv"
        $errorDir = Join-Path $pipelineDir "error_analysis"
        & $python -X utf8 -m a11code.analyze_errors `
            --predictions $predictions `
            --output-dir $errorDir
        & $python -X utf8 -m a11code.export_error_examples `
            --predictions $predictions `
            --output-dir (Join-Path $errorDir "examples")
    }
} finally {
    Pop-Location
}
