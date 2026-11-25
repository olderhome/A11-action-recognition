param(
    [int]$Segments = 4
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$partRoot = Join-Path $projectRoot "runtime\model_weight_parts"
$cacheRoot = Join-Path $env:USERPROFILE ".cache\torch\hub\checkpoints"
$mmactionCheckpoints = Join-Path $projectRoot "mmaction2-main\checkpoints"
New-Item -ItemType Directory -Force `
    -Path $partRoot,$cacheRoot,$mmactionCheckpoints | Out-Null

$applicationWeights = @(
    @{
        Name = "tsn_r50_kinetics400.pth"
        Url = "https://download.openmmlab.com/mmaction/v1.0/recognition/tsn/tsn_imagenet-pretrained-r50_8xb32-1x1x8-100e_kinetics400-rgb/tsn_imagenet-pretrained-r50_8xb32-1x1x8-100e_kinetics400-rgb_20220906-2692d16c.pth"
        Size = 97641409
    },
    @{
        Name = "r2plus1d_r34_kinetics400.pth"
        Url = "https://download.openmmlab.com/mmaction/v1.0/recognition/r2plus1d/r2plus1d_r34_8xb8-8x8x1-180e_kinetics400-rgb/r2plus1d_r34_8xb8-8x8x1-180e_kinetics400-rgb_20220812-47cfe041.pth"
        Size = 255400285
    }
)

foreach ($file in $applicationWeights) {
    $target = Join-Path $mmactionCheckpoints $file.Name
    if ((Test-Path -LiteralPath $target) -and
        ((Get-Item -LiteralPath $target).Length -eq $file.Size)) {
        Write-Host "Already complete: $($file.Name)"
        continue
    }
    & curl.exe -L --retry 5 --retry-delay 3 `
        --connect-timeout 30 --max-time 1800 `
        --silent --show-error $file.Url -o $target
    if ($LASTEXITCODE -ne 0 -or
        (Get-Item -LiteralPath $target).Length -ne $file.Size) {
        throw "Download failed: $($file.Name)"
    }
    Write-Host "Downloaded: $($file.Name)"
}

$files = @(
    @{
        Name = "r3d_18-b3b3357e.pth"
        Url = "https://download.pytorch.org/models/r3d_18-b3b3357e.pth"
        Size = 133546016
    },
    @{
        Name = "r2plus1d_18-91a641e6.pth"
        Url = "https://download.pytorch.org/models/r2plus1d_18-91a641e6.pth"
        Size = 126162996
    }
)

foreach ($file in $files) {
    $target = Join-Path $cacheRoot $file.Name
    if ((Test-Path -LiteralPath $target) -and
        ((Get-Item -LiteralPath $target).Length -eq $file.Size)) {
        Write-Host "Already complete: $($file.Name)"
        continue
    }
    $fileParts = Join-Path $partRoot $file.Name
    New-Item -ItemType Directory -Force -Path $fileParts | Out-Null
    $segmentSize = [math]::Ceiling($file.Size / $Segments)
    $processes = @()
    for ($index = 0; $index -lt $Segments; $index++) {
        $start = [int64]$index * $segmentSize
        $end = [math]::Min($file.Size - 1, $start + $segmentSize - 1)
        $partPath = Join-Path $fileParts (
            "part{0:D2}" -f $index)
        $process = Start-Process `
            -FilePath "curl.exe" `
            -ArgumentList @(
                "-L", "-r", "$start-$end",
                "--retry", "5", "--retry-delay", "3",
                "--connect-timeout", "30", "--max-time", "1800",
                "--silent", "--show-error",
                $file.Url, "-o", $partPath
            ) `
            -WindowStyle Hidden `
            -PassThru
        $processes += $process
    }
    $processes | Wait-Process

    $buffer = New-Object byte[] (4MB)
    $output = [System.IO.File]::Open(
        $target, [System.IO.FileMode]::Create,
        [System.IO.FileAccess]::Write)
    try {
        for ($index = 0; $index -lt $Segments; $index++) {
            $partPath = Join-Path $fileParts (
                "part{0:D2}" -f $index)
            $input = [System.IO.File]::OpenRead($partPath)
            try {
                while (($read = $input.Read(
                            $buffer, 0, $buffer.Length)) -gt 0) {
                    $output.Write($buffer, 0, $read)
                }
            } finally {
                $input.Dispose()
            }
        }
    } finally {
        $output.Dispose()
    }
    if ((Get-Item -LiteralPath $target).Length -ne $file.Size) {
        throw "Size mismatch for $($file.Name)"
    }
    Remove-Item -LiteralPath $fileParts -Recurse
    Write-Host "Downloaded: $($file.Name)"
}
