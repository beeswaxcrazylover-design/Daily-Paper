param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^(https://github\.com/|git@github\.com:)')]
    [string]$RepositoryUrl
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepositoryRoot

if (-not (Test-Path ".git")) {
    throw "Git repository not found at $RepositoryRoot"
}

$existingOrigin = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0) {
    git remote set-url origin $RepositoryUrl
}
else {
    git remote add origin $RepositoryUrl
}

git branch -M main
git push -u origin main
exit $LASTEXITCODE

