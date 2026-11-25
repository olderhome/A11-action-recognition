$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pidFile = Join-Path $projectRoot "outputs\comparison_server\server.pid"

if (-not (Test-Path -LiteralPath $pidFile)) {
    Write-Host "No comparison app PID file found."
    exit 0
}

$serverPid = [int](Get-Content -LiteralPath $pidFile -Raw)
$process = Get-Process -Id $serverPid -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Id $serverPid
    Write-Host "Stopped comparison app process $serverPid."
} else {
    Write-Host "Comparison app process is not running."
}
Remove-Item -LiteralPath $pidFile
