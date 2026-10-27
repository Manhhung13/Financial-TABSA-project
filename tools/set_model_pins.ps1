param(
    [string]$FastModel = 'gpt-6-luna',
    [string]$DeepModel = 'gpt-6.1-sol',
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$agents = Join-Path $repo '.codex\agents'
$roles = @{'scout'=$FastModel;'data_worker'=$FastModel;'implementer'=$DeepModel;'ml_architect'=$DeepModel;'reviewer'=$DeepModel}
foreach ($entry in $roles.GetEnumerator()) {
  $path = Join-Path $agents ($entry.Key + '.toml')
  if (-not (Test-Path $path)) { throw "Missing agent file: $path" }
  $old = Get-Content -LiteralPath $path -Raw -Encoding UTF8
  $new = [regex]::Replace($old, '(?m)^model\s*=.*\r?\n', '')
  $new = $new.TrimEnd() + "`nmodel = `"$($entry.Value)`"`n"
  Write-Host ("{0} -> {1}" -f $entry.Key,$entry.Value)
  if (-not $DryRun) {
    Copy-Item -LiteralPath $path -Destination ($path + '.bak') -Force
    Set-Content -LiteralPath $path -Value $new -Encoding utf8
  }
}
if ($DryRun) { Write-Host 'DRY RUN: no files changed' } else { Write-Host 'Model pins written. Verify entitlements before running Codex.' }
