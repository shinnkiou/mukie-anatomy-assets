$ErrorActionPreference = 'Stop'
$base = Split-Path -Parent $MyInvocation.MyCommand.Path
$configDir = Join-Path $base 'config'
$configPath = Join-Path $configDir 'discord.local.json'
New-Item -ItemType Directory -Path $configDir -Force | Out-Null

$guildId = Read-Host 'Discord server (guild) ID'
if ($guildId -notmatch '^\d{17,20}$') {
  throw 'Guild ID must be a 17-20 digit Discord snowflake.'
}

$data = [ordered]@{
  guild_id = [Int64]$guildId
  channel_id = $null
  user_id = $null
  configured_at = (Get-Date).ToString('o')
}
$data | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $configPath -Encoding UTF8
Write-Host ''
Write-Host 'Discord relay local config saved.' -ForegroundColor Green
Write-Host 'Next: run SETUP_DISCORD_TOKEN.bat, then START_PROJECT_RELAY_WITH_DISCORD.bat.'
Write-Host 'After the bot is online, open the approved control channel and run /relay bind once.'
