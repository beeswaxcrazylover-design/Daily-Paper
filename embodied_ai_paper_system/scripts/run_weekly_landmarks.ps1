$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir ("{0}.log" -f (Get-Date -Format "yyyy-MM-dd"))

function Show-FailureMessage {
    param(
        [string]$Message
    )
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.MessageBox]::Show(
        "$Message`n`nLog file:`n$LogFile",
        "Weekly landmark task failed",
        "OK",
        "Error"
    ) | Out-Null
}

if (-not (Test-Path $Python)) {
    Show-FailureMessage "Virtual environment not found. Complete the README setup first."
    exit 1
}

try {
    Set-Location $ProjectRoot
    & $Python "main.py" "landmarks"
    $ExitCode = $LASTEXITCODE
    if ($ExitCode -ne 0) {
        Show-FailureMessage "Weekly landmark task exited with code $ExitCode."
    }
    exit $ExitCode
}
catch {
    Show-FailureMessage $_.Exception.Message
    exit 1
}
