function Resolve-A11Python {
    param([Parameter(Mandatory = $true)][string]$ProjectRoot)

    $candidates = @(
        (Join-Path $ProjectRoot "runtime\python311\python.exe"),
        (Join-Path $ProjectRoot ".venv\Scripts\python.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) {
        return $launcher.Source
    }
    throw "Python 3.10/3.11 was not found. Run .\setup.ps1 first."
}
