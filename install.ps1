param(
    [string]$Destination = (Join-Path $HOME ".claude\skills")
)

$ErrorActionPreference = "Stop"

$source = Join-Path $PSScriptRoot "skills"
if (-not (Test-Path $source)) {
    throw "skills directory not found: $source"
}

New-Item -ItemType Directory -Force $Destination | Out-Null

Get-ChildItem $source -Directory | ForEach-Object {
    Copy-Item $_.FullName -Destination $Destination -Recurse -Force
    Write-Host "Installed $($_.Name)"
}

Write-Host ""
Write-Host "Done. Restart Claude Code or start a new session to load the skills."
