$ErrorActionPreference = "Stop"

$marketplace = Join-Path $PSScriptRoot "plugins"
if (-not (Test-Path $marketplace)) {
    throw "plugins directory not found: $marketplace"
}

Write-Host "Adding local marketplace..."
claude plugin marketplace add $marketplace
if ($LASTEXITCODE -ne 0) {
    Write-Host "Marketplace may already be configured; continuing."
}

Write-Host "Installing pm-skills..."
claude plugin install pm-skills@gov-skill-bundle -y

Write-Host "Installing product-skills..."
claude plugin install product-skills@gov-skill-bundle -y

Write-Host ""
Write-Host "Done. Restart Claude Code to load the plugins."
