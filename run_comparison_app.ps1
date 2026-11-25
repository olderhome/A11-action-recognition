$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot "runtime\python311\python.exe"
$app = Join-Path $projectRoot "mmaction2-main\a11_tools\comparison_app.py"
$logDir = Join-Path $projectRoot "outputs\comparison_server"
$pidFile = Join-Path $logDir "server.pid"
$url = "http://127.0.0.1:7860"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$running = Test-NetConnection -ComputerName 127.0.0.1 -Port 7860 `
    -InformationLevel Quiet -WarningAction SilentlyContinue

if (-not $running) {
    $process = Start-Process `
        -FilePath $python `
        -ArgumentList @(
            "-X", "utf8", $app,
            "--host", "127.0.0.1",
            "--port", "7860",
            "--device", "cuda:0"
        ) `
        -WorkingDirectory $projectRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "server.log") `
        -RedirectStandardError (Join-Path $logDir "server.err") `
        -PassThru
    Set-Content -LiteralPath $pidFile -Value $process.Id -Encoding ascii
}

$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $health = Invoke-RestMethod -Uri "$url/api/health" -TimeoutSec 2
        if ($health.ok) {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

if (-not $ready) {
    throw "Comparison app did not start. Check $logDir\server.err"
}

Start-Process $url
Write-Host "Comparison app: $url"
Write-Host "GPU: $($health.gpu)"
