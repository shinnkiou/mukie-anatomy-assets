$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Tab = [char]9

$Snapshots = @(
    [pscustomobject]@{
        Label = "FULL"
        Path  = "C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT\CSMC_FULL_SNAPSHOT_20260914_214659.zip"
    },
    [pscustomobject]@{
        Label = "FOCUSED"
        Path  = "C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT\CSMC_FULL_SNAPSHOT_FOCUSED_20260914_232435.zip"
    }
)

$PrivateRoot = "C:\Users\nurun\CSMC_ANALYSIS\PRIVATE_FULL_SNAPSHOT"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunRoot = Join-Path $PrivateRoot ("REVIEWER_P0_" + $Stamp)
$ExtractRoot = Join-Path $RunRoot "EXTRACTED_TARGETED"
$Reports = Join-Path $RunRoot "REPORTS"

New-Item -ItemType Directory -Force -Path $RunRoot, $ExtractRoot, $Reports | Out-Null

function Write-Status {
    param([string]$Text)
    Write-Host $Text -ForegroundColor Cyan
}

function Find-7Zip {
    $items = @()
    $cmd = Get-Command 7z.exe -ErrorAction SilentlyContinue
    if ($cmd) { $items += $cmd.Source }
    $items += @(
        "C:\Program Files\7-Zip\7z.exe",
        "C:\Program Files (x86)\7-Zip\7z.exe"
    )
    foreach ($p in $items | Select-Object -Unique) {
        if ($p -and (Test-Path -LiteralPath $p)) { return $p }
    }
    return $null
}

function Find-Rg {
    $cmd = Get-Command rg.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $roots = @(
        (Join-Path $env:USERPROFILE "CSMC_ANALYSIS\Tools"),
        (Join-Path $env:LOCALAPPDATA "Programs")
    )
    foreach ($r in $roots) {
        if (-not (Test-Path -LiteralPath $r)) { continue }
        $hit = Get-ChildItem -LiteralPath $r -Recurse -File -Filter "rg.exe" -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }
    return $null
}

function Get-PythonCommand {
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        & $py.Source -3 -c "import sys; print(sys.executable)" *> $null
        if ($LASTEXITCODE -eq 0) {
            return [pscustomobject]@{ Exe = $py.Source; Prefix = @("-3") }
        }
    }

    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($python) {
        & $python.Source -c "import sys; print(sys.executable)" *> $null
        if ($LASTEXITCODE -eq 0) {
            return [pscustomobject]@{ Exe = $python.Source; Prefix = @() }
        }
    }

    return $null
}

function Invoke-Python {
    param(
        [Parameter(Mandatory=$true)]$Python,
        [Parameter(Mandatory=$true)][string[]]$Args
    )
    $all = @()
    $all += $Python.Prefix
    $all += $Args
    & $Python.Exe @all
    if ($LASTEXITCODE -ne 0) {
        throw "Python exited with code $LASTEXITCODE"
    }
}

function Parse-7ZipSlt {
    param(
        [Parameter(Mandatory=$true)]
        [AllowEmptyString()]
        [AllowEmptyCollection()]
        [string[]]$Lines,
        [Parameter(Mandatory=$true)][string]$ArchivePath
    )

    $records = New-Object System.Collections.ArrayList
    $current = @{}

    foreach ($line in $Lines) {
        if ([string]::IsNullOrWhiteSpace($line)) {
            if ($current.ContainsKey("Path")) {
                $p = [string]$current["Path"]
                if ($p -and $p -ne $ArchivePath) {
                    $size = 0L
                    if ($current.ContainsKey("Size")) {
                        [long]::TryParse([string]$current["Size"], [ref]$size) | Out-Null
                    }
                    $attr = ""
                    if ($current.ContainsKey("Attributes")) { $attr = [string]$current["Attributes"] }
                    $isDir = ($attr -match "D") -or $p.EndsWith("\") -or $p.EndsWith("/")
                    if (-not $isDir) {
                        [void]$records.Add([pscustomobject]@{
                            Path = $p
                            Size = $size
                            Attributes = $attr
                        })
                    }
                }
            }
            $current = @{}
            continue
        }

        $idx = $line.IndexOf(" = ")
        if ($idx -gt 0) {
            $k = $line.Substring(0, $idx).Trim()
            $v = $line.Substring($idx + 3)
            $current[$k] = $v
        }
    }

    if ($current.ContainsKey("Path")) {
        $p = [string]$current["Path"]
        if ($p -and $p -ne $ArchivePath) {
            $size = 0L
            if ($current.ContainsKey("Size")) {
                [long]::TryParse([string]$current["Size"], [ref]$size) | Out-Null
            }
            $attr = ""
            if ($current.ContainsKey("Attributes")) { $attr = [string]$current["Attributes"] }
            $isDir = ($attr -match "D") -or $p.EndsWith("\") -or $p.EndsWith("/")
            if (-not $isDir) {
                [void]$records.Add([pscustomobject]@{
                    Path = $p
                    Size = $size
                    Attributes = $attr
                })
            }
        }
    }

    return @($records)
}

$SevenZip = Find-7Zip
$Rg = Find-Rg
$Python = Get-PythonCommand

$ToolRows = @()
$ToolRows += [pscustomobject]@{ tool="7zip"; status=($(if($SevenZip){"FOUND"}else{"MISSING"})); path=$SevenZip }
$ToolRows += [pscustomobject]@{ tool="ripgrep"; status=($(if($Rg){"FOUND"}else{"OPTIONAL_MISSING"})); path=$Rg }
$ToolRows += [pscustomobject]@{ tool="python"; status=($(if($Python){"FOUND"}else{"MISSING"})); path=($(if($Python){$Python.Exe}else{""})) }

$ToolRows | Export-Csv -LiteralPath (Join-Path $Reports "tool_status.tsv") -Delimiter $Tab -NoTypeInformation -Encoding UTF8

if (-not $SevenZip) {
    throw "7-Zip not found. Install 7-Zip or add 7z.exe to PATH."
}
if (-not $Python) {
    throw "Python not found."
}

$Manifest = @()
$InputArgs = @()
$TextExts = @(
    ".txt",".md",".json",".jsonl",".tsv",".csv",".log",
    ".xml",".yaml",".yml",".ini",".cfg",".ps1",".bat",".cmd",
    ".py",".java",".c",".cc",".cpp",".h",".hpp",".asm",".s"
)
$MaxSingleFile = 24MB
$MaxExtractTotal = 350MB

foreach ($Snap in $Snapshots) {
    Write-Status ("=== " + $Snap.Label + " ===")
    Write-Host "Reviewer build: P0.2 (array-count StrictMode fix)"

    if (-not (Test-Path -LiteralPath $Snap.Path)) {
        Write-Host ("[MISSING] " + $Snap.Path) -ForegroundColor Red
        $Manifest += [pscustomobject]@{
            snapshot=$Snap.Label; archive=$Snap.Path; archive_sha256="";
            archive_bytes=0; member=""; member_bytes=0; selected="NO_ARCHIVE"
        }
        continue
    }

    $ArchiveInfo = Get-Item -LiteralPath $Snap.Path
    $ArchiveHash = (Get-FileHash -LiteralPath $Snap.Path -Algorithm SHA256).Hash.ToLowerInvariant()

    Write-Host ("SHA256: " + $ArchiveHash)
    Write-Host ("Bytes : " + $ArchiveInfo.Length)

    $ListRawPath = Join-Path $Reports ($Snap.Label + "_7zip_slt.txt")
    $ListLines = @(& $SevenZip l -slt -- $Snap.Path | ForEach-Object { [string]$_ })
    if ($LASTEXITCODE -ne 0) {
        throw "7-Zip listing failed for $($Snap.Path)"
    }
    $ListLines | Set-Content -LiteralPath $ListRawPath -Encoding UTF8

    if ($null -eq $ListLines -or $ListLines.Count -eq 0) {
        throw "7-Zip returned an empty listing for $($Snap.Path)"
    }

    $Entries = Parse-7ZipSlt -Lines $ListLines -ArchivePath $Snap.Path
    $Selected = @()
    $SelectedTotal = 0L

    foreach ($e in $Entries) {
        $ext = [IO.Path]::GetExtension($e.Path).ToLowerInvariant()
        $isText = $TextExts -contains $ext
        $take = $false

        if ($isText -and $e.Size -le $MaxSingleFile) {
            if (($SelectedTotal + $e.Size) -le $MaxExtractTotal) {
                $take = $true
                $Selected += $e
                $SelectedTotal += $e.Size
            }
        }

        $Manifest += [pscustomobject]@{
            snapshot=$Snap.Label
            archive=$Snap.Path
            archive_sha256=$ArchiveHash
            archive_bytes=$ArchiveInfo.Length
            member=$e.Path
            member_bytes=$e.Size
            selected=($(if($take){"YES"}else{"NO"}))
        }
    }

    $SnapExtract = Join-Path $ExtractRoot $Snap.Label
    New-Item -ItemType Directory -Force -Path $SnapExtract | Out-Null

    $ListFile = Join-Path $RunRoot ($Snap.Label + "_extract_list.txt")
    $Selected.Path | Set-Content -LiteralPath $ListFile -Encoding UTF8

    Write-Host ("Selected text artifacts: " + $Selected.Count)
    Write-Host ("Selected bytes         : " + $SelectedTotal)

    if ($Selected.Count -gt 0) {
        & $SevenZip x -y -aoa -scsUTF-8 ("-o" + $SnapExtract) -- $Snap.Path ("@" + $ListFile)
        if ($LASTEXITCODE -ne 0) {
            throw "7-Zip selective extraction failed for $($Snap.Path)"
        }
    }

    $InputArgs += @("--input", ($Snap.Label + "=" + $SnapExtract))
}

$Manifest |
    Export-Csv -LiteralPath (Join-Path $Reports "manifest.tsv") -Delimiter $Tab -NoTypeInformation -Encoding UTF8

if ($Rg) {
    Write-Status "Running targeted ripgrep pass..."
    $Pattern = "consumer|deserializ|decode|parse|reader|loader|character payload|internal object|construct|factory|PW3DModelDataLoader|PWCanvas3DModelLoader|PW3DLayerUtility|Canvas3DModelLoader|ModelData3D|glBufferSubData|vertex buffer|transform|matrix|bone|weight|joint|skin|deform|palette|skeleton|quaternion"
    $RgOut = Join-Path $Reports "rg_targeted_raw.txt"
    & $Rg -n -i -S --no-heading --max-count 80 -e $Pattern $ExtractRoot |
        Set-Content -LiteralPath $RgOut -Encoding UTF8
}

Write-Status "Running Python evidence classifier..."

$PyArgs = @(
    (Join-Path $ScriptDir "02_ANALYZE_TARGETED_SNAPSHOT.py"),
    "--known", (Join-Path $ScriptDir "KNOWN_FACTS.json"),
    "--out", $Reports
)
$PyArgs += $InputArgs

Invoke-Python -Python $Python -Args $PyArgs

$Targets = Join-Path $Reports "ghidra_targets.txt"

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host "CSMC FULL SNAPSHOT REVIEWER P0 COMPLETE" -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
Write-Host ("Reports: " + $Reports)
Write-Host ""
Write-Host "ChatGPTへ基本的に送るもの:"
Write-Host "  SUMMARY.md"
Write-Host "  consumer_candidates.tsv"
Write-Host "  novel_evidence.tsv"
Write-Host "  ghidra_targets.txt"
Write-Host "  evidence.json"

if (Test-Path -LiteralPath $Targets) {
    $TargetLines = @(
        Get-Content -LiteralPath $Targets |
            Where-Object { $_ -and (-not $_.StartsWith("#")) }
    )
    Write-Host ""
    Write-Host ("Ghidra target lines: " + $TargetLines.Count)
    if ($TargetLines.Count -gt 0) {
        Write-Host "新規RVA候補があります。次はtargeted Ghidra passです。" -ForegroundColor Yellow
    } else {
        Write-Host "新規Ghidra targetは出ませんでした。novel_evidence.tsvを先に確認します。" -ForegroundColor Yellow
    }
}

Start-Process explorer.exe $Reports
