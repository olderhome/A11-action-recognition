$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$dataRoot = Join-Path $projectRoot "mmaction2-main\data\ucf101"
$archive = Join-Path $dataRoot "UCF-101.zip"
$extractRoot = Join-Path $dataRoot "extracted"
$videoRoot = Join-Path $dataRoot "videos"
$sevenZip = "C:\Program Files\7-Zip\7z.exe"
. (Join-Path $projectRoot "a11_env.ps1")
$python = Resolve-A11Python -ProjectRoot $projectRoot

if (-not (Test-Path -LiteralPath $archive)) {
    throw "UCF101 archive is missing: $archive"
}
if (-not (Test-Path -LiteralPath $sevenZip)) {
    throw "7-Zip executable is missing: $sevenZip"
}

if (-not (Test-Path -LiteralPath $videoRoot)) {
    if (Test-Path -LiteralPath $extractRoot) {
        Remove-Item -LiteralPath $extractRoot -Recurse
    }
    New-Item -ItemType Directory -Force -Path $extractRoot | Out-Null
    & $sevenZip x $archive "-o$extractRoot" -y
    if ($LASTEXITCODE -ne 0) {
        throw "7-Zip extraction failed with exit code $LASTEXITCODE"
    }
    $extractedVideoRoot = Join-Path $extractRoot "UCF-101"
    if (-not (Test-Path -LiteralPath $extractedVideoRoot)) {
        throw "UCF-101 directory not found after extraction."
    }
    Move-Item -LiteralPath $extractedVideoRoot -Destination $videoRoot
}

$classDirectories = Get-ChildItem -Directory -LiteralPath $videoRoot
$videos = Get-ChildItem -Recurse -File -LiteralPath $videoRoot -Filter "*.avi"
$summary = [pscustomobject]@{
    Classes = $classDirectories.Count
    Videos = $videos.Count
    VideoRoot = $videoRoot
}
$summary | Format-List

if ($summary.Classes -ne 101) {
    throw "Expected 101 UCF101 classes, got $($summary.Classes)"
}
if ($summary.Videos -ne 13320) {
    throw "Expected 13320 UCF101 videos, got $($summary.Videos)"
}

Push-Location $projectRoot
try {
    & $python -X utf8 -m a11code.build_manifest
} finally {
    Pop-Location
}
