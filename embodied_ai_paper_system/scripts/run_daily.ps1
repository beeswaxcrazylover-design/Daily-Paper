$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "Virtual environment not found. Complete the README setup first."
}

Set-Location $ProjectRoot
& $Python "main.py" "daily"
exit $LASTEXITCODE
