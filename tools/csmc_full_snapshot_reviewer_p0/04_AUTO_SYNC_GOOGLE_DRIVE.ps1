param(
    [Parameter(Mandatory=$true)][string]$RunRoot
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$Reports = Join-Path $RunRoot "REPORTS"
if (-not (Test-Path -LiteralPath $Reports)) {
    throw "REPORTS folder not found: $Reports"
}

function Add-Candidate([System.Collections.ArrayList]$List, [string]$Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return }
    if (Test-Path -LiteralPath $Path) {
        if (-not $List.Contains($Path)) { [void]$List.Add($Path) }
    }
}

function Find-DriveRoot {
    $Candidates = New-Object System.Collections.ArrayList

    if ($env:CSMC_GOOGLE_DRIVE_ROOT) {
        Add-Candidate $Candidates $env:CSMC_GOOGLE_DRIVE_ROOT
    }

    $ConfigFile = Join-Path $env:USERPROFILE "CSMC_ANALYSIS\GOOGLE_DRIVE_ROOT.txt"
    if (Test-Path -LiteralPath $ConfigFile) {
        $Configured = (Get-Content -LiteralPath $ConfigFile -Raw).Trim()
        Add-Candidate $Candidates $Configured
    }

    foreach ($Drive in (Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue)) {
        $Root = $Drive.Root
        Add-Candidate $Candidates (Join-Path $Root "My Drive")
        Add-Candidate $Candidates (Join-Path $Root ([string][char]0x30DE + [char]0x30A4 + [char]0x30C9 + [char]0x30E9 + [char]0x30A4 + [char]0x30D6))
        $RootResearch = Join-Path $Root "CSMC_RESEARCH"
        if (Test-Path -LiteralPath $RootResearch) { return $Root }
    }

    Add-Candidate $Candidates (Join-Path $env:USERPROFILE "My Drive")
    Add-Candidate $Candidates (Join-Path $env:USERPROFILE "Google Drive\My Drive")
    Add-Candidate $Candidates (Join-Path $env:USERPROFILE "Google Drive")

    foreach ($C in $Candidates) {
        $ExistingResearch = Join-Path $C "CSMC_RESEARCH"
        if (Test-Path -LiteralPath $ExistingResearch) { return $C }
    }

    foreach ($C in $Candidates) {
        try {
            $Probe = Join-Path $C ".csmc_drive_write_probe.tmp"
            "probe" | Set-Content -LiteralPath $Probe -Encoding ASCII
            Remove-Item -LiteralPath $Probe -Force -ErrorAction SilentlyContinue
            return $C
        } catch { }
    }
    return $null
}

$DriveRoot = Find-DriveRoot
$StatusFile = Join-Path $Reports "DRIVE_SYNC_STATUS.txt"

if (-not $DriveRoot) {
    @(
        "status=DRIVE_NOT_DETECTED",
        "action=Install/sign in to Google Drive for desktop once, then rerun reviewer.",
        "no_data_lost=true",
        ("run_root=" + $RunRoot)
    ) | Set-Content -LiteralPath $StatusFile -Encoding UTF8
    Write-Host "Google Drive desktop folder not detected. Local reports are safe." -ForegroundColor Yellow
    exit 0
}

$ResearchRoot = Join-Path $DriveRoot "CSMC_RESEARCH"
$ReportsRoot = Join-Path $ResearchRoot "REPORTS"
$CurrentRoot = Join-Path $ResearchRoot "00_CURRENT"
$ArchiveRoot = Join-Path $ResearchRoot "ARCHIVE"
New-Item -ItemType Directory -Force -Path $ResearchRoot,$ReportsRoot,$CurrentRoot,$ArchiveRoot | Out-Null

$RunName = Split-Path -Leaf $RunRoot
$DestRun = Join-Path $ReportsRoot $RunName
New-Item -ItemType Directory -Force -Path $DestRun | Out-Null

Write-Host ("Google Drive root : " + $DriveRoot)
Write-Host ("Drive report dest : " + $DestRun)

# Copy only reports, not extracted snapshots or proprietary binary payloads.
robocopy $Reports $DestRun /E /R:2 /W:2 /COPY:DAT /DCOPY:DAT /NFL /NDL /NP | Out-Null
$RoboRC = $LASTEXITCODE
if ($RoboRC -ge 8) { throw "robocopy failed with exit code $RoboRC" }

$Packet = Join-Path $Reports "P1_CHATGPT_PACKET_CURRENT.md"\r\nif (-not (Test-Path -LiteralPath $Packet)) { $Packet = Join-Path $Reports "P1_CHATGPT_PACKET_CURRENT.md"\r\nif (-not (Test-Path -LiteralPath $Packet)) { $Packet = Join-Path $Reports "CHATGPT_PACKET_P08.md" }\r\nif (-not (Test-Path -LiteralPath $Packet)) { $Packet = Join-Path $Reports "CHATGPT_PACKET.md" }\r\n$Summary = Join-Path $Reports "P1_SUMMARY_CURRENT.md"\r\nif (-not (Test-Path -LiteralPath $Summary)) { $Summary = Join-Path $Reports "SUMMARY_P08.md" }\r\nif (-not (Test-Path -LiteralPath $Summary)) { $Summary = Join-Path $Reports "SUMMARY.md" }\r\n\r\nif (Test-Path -LiteralPath $Packet) {
    Copy-Item -LiteralPath $Packet -Destination (Join-Path $CurrentRoot "CHATGPT_PACKET_CURRENT.md") -Force
}
if (Test-Path -LiteralPath $Summary) {
    Copy-Item -LiteralPath $Summary -Destination (Join-Path $CurrentRoot "SUMMARY_CURRENT.md") -Force
}

$Pointer = [ordered]@{
    schema = "csmc_drive_pointer_v1"
    updated_utc = [DateTime]::UtcNow.ToString("o")
    reviewer_run = $RunName
    local_run_root = $RunRoot
    drive_root = $DriveRoot
    drive_research_root = $ResearchRoot
    drive_reports_path = $DestRun
    current_packet = (Join-Path $CurrentRoot "CHATGPT_PACKET_CURRENT.md")
    current_summary = (Join-Path $CurrentRoot "SUMMARY_CURRENT.md")
    semantic_promotion = $false
}
$Pointer | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $CurrentRoot "CURRENT_POINTER.json") -Encoding UTF8

$PacketSha = ""
if (Test-Path -LiteralPath $Packet) {
    $PacketSha = (Get-FileHash -LiteralPath $Packet -Algorithm SHA256).Hash.ToLowerInvariant()
}

@(
    "status=COPIED_TO_GOOGLE_DRIVE_DESKTOP",
    ("drive_root=" + $DriveRoot),
    ("research_root=" + $ResearchRoot),
    ("reports_dest=" + $DestRun),
    ("packet_sha256=" + $PacketSha),
    "note=Google Drive for desktop uploads this synchronized folder to cloud when online."
) | Set-Content -LiteralPath $StatusFile -Encoding UTF8

Write-Host "Drive sync handoff complete." -ForegroundColor Green
Write-Host ("Current packet: " + (Join-Path $CurrentRoot "CHATGPT_PACKET_CURRENT.md"))
