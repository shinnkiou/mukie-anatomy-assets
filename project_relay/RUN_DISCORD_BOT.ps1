$ErrorActionPreference = 'Stop'
$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$tokenPath = Join-Path $base 'private\discord_token.dpapi'
$configPath = Join-Path $base 'config\discord.local.json'

if (-not (Test-Path -LiteralPath $tokenPath)) {
  throw 'Discord token is not configured. Run SETUP_DISCORD_TOKEN.bat first.'
}
if (-not (Test-Path -LiteralPath $configPath)) {
  throw 'Discord guild is not configured. Run CONFIGURE_DISCORD_RELAY.bat first.'
}

$encrypted = (Get-Content -LiteralPath $tokenPath -Raw).Trim()
$secure = ConvertTo-SecureString $encrypted
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
  $plain = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  if ([string]::IsNullOrWhiteSpace($plain)) { throw 'Discord token could not be decrypted.' }
  $env:PROJECT_RELAY_DISCORD_TOKEN = $plain

  if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 (Join-Path $base 'discord_bot.py')
    exit $LASTEXITCODE
  }
  if (Get-Command python -ErrorAction SilentlyContinue) {
    & python (Join-Path $base 'discord_bot.py')
    exit $LASTEXITCODE
  }
  throw 'Python 3 was not found.'
}
finally {
  if ($bstr -ne [IntPtr]::Zero) {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
  Remove-Item Env:PROJECT_RELAY_DISCORD_TOKEN -ErrorAction SilentlyContinue
  $plain = $null
}
