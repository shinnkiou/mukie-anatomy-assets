$ErrorActionPreference = 'Stop'
$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$privateDir = Join-Path $base 'private'
$tokenPath = Join-Path $privateDir 'discord_token.dpapi'
New-Item -ItemType Directory -Path $privateDir -Force | Out-Null

Write-Host 'Paste the Discord Bot token. It will be encrypted for the current Windows user.'
$secure = Read-Host 'Discord Bot token' -AsSecureString
if ($secure.Length -lt 20) {
  throw 'Token input looks too short.'
}
$secure | ConvertFrom-SecureString | Set-Content -LiteralPath $tokenPath -Encoding UTF8
Write-Host ''
Write-Host 'Discord Bot token saved with Windows DPAPI protection.' -ForegroundColor Green
Write-Host 'The plaintext token was not written to disk.'
