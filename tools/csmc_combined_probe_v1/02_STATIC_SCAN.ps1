$ErrorActionPreference="Stop"
Set-StrictMode -Version 2.0
Add-Type -AssemblyName System.Windows.Forms

$Base=Join-Path $env:USERPROFILE "CSMC_ANALYSIS"
$Stamp=Get-Date -Format "yyyyMMdd_HHmmss"
$Out=Join-Path $Base ("COMBINED_STATIC_SCAN_"+$Stamp)
New-Item -ItemType Directory -Path $Out -Force|Out-Null

$InputPath=""
if($args.Count -gt 0 -and $args[0]){$InputPath=$args[0]}
if([string]::IsNullOrWhiteSpace($InputPath)){
  $dlg=New-Object System.Windows.Forms.OpenFileDialog
  $dlg.Title="Select CSMC file"
  $dlg.Filter="CSMC files (*.csmc)|*.csmc|All files (*.*)|*.*"
  if($dlg.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK){throw "No file selected"}
  $InputPath=$dlg.FileName
}

$InputPath=(Resolve-Path -LiteralPath $InputPath).Path
$fi=Get-Item -LiteralPath $InputPath
if($fi.Length -gt 805306368){throw "File exceeds 768 MiB. Select the CSMC, not an apitrace file."}

$sha=(Get-FileHash -LiteralPath $InputPath -Algorithm SHA256).Hash.ToLowerInvariant()
$bytes=[IO.File]::ReadAllBytes($InputPath)
$latin=[Text.Encoding]::GetEncoding(28591).GetString($bytes)
$utf16=[Text.Encoding]::Unicode.GetString($bytes)

function CountText([string]$hay,[string]$needle){
  if([string]::IsNullOrEmpty($needle)){return 0}
  $count=0;$pos=0
  while($true){
    $idx=$hay.IndexOf($needle,$pos,[StringComparison]::OrdinalIgnoreCase)
    if($idx -lt 0){break}
    $count++
    $pos=$idx+[Math]::Max(1,$needle.Length)
  }
  return $count
}

$markers=@(
  [pscustomobject]@{C="ENGINE_ASSET_PACKAGE";N="CSFCHUNK";P="CSFCHUNK";W=6},
  [pscustomobject]@{C="ENGINE_ASSET_PACKAGE";N="CHNKHead";P="CHNKHead";W=4},
  [pscustomobject]@{C="ENGINE_ASSET_PACKAGE";N="CHNKFoot";P="CHNKFoot";W=4},
  [pscustomobject]@{C="ENGINE_ASSET_PACKAGE";N="CHNKExta";P="CHNKExta";W=4},
  [pscustomobject]@{C="ENGINE_ASSET_PACKAGE";N="CHNKSQLi";P="CHNKSQLi";W=4},
  [pscustomobject]@{C="ENGINE_ASSET_PACKAGE";N="ExternalChunk";P="ExternalChunk";W=4},
  [pscustomobject]@{C="ENGINE_ASSET_PACKAGE";N="BankData";P="BankData";W=3},
  [pscustomobject]@{C="ENGINE_ASSET_PACKAGE";N="Layer3DModelData";P="Layer3DModelData";W=4},
  [pscustomobject]@{C="ENGINE_ASSET_PACKAGE";N="Canvas3DModelLoader";P="Canvas3DModelLoader";W=5},
  [pscustomobject]@{C="ENGINE_ASSET_PACKAGE";N="ModelData3D";P="ModelData3D";W=4},

  [pscustomobject]@{C="FBX_SCENE_MODEL";N="ModelInfo3D";P="ModelInfo3D";W=4},
  [pscustomobject]@{C="FBX_SCENE_MODEL";N="ModelNodeInfo3D";P="ModelNodeInfo3D";W=5},
  [pscustomobject]@{C="FBX_SCENE_MODEL";N="DessindollBoneInfo";P="DessindollBoneInfo";W=6},
  [pscustomobject]@{C="FBX_SCENE_MODEL";N="DessindollShapeInfo";P="DessindollShapeInfo";W=5},
  [pscustomobject]@{C="FBX_SCENE_MODEL";N="NodeName";P="NodeName";W=3},
  [pscustomobject]@{C="FBX_SCENE_MODEL";N="NodeRotationR";P="NodeRotationR";W=3},
  [pscustomobject]@{C="FBX_SCENE_MODEL";N="KaydaraFBX";P="Kaydara FBX Binary";W=20},
  [pscustomobject]@{C="FBX_SCENE_MODEL";N="FBXHeaderExtension";P="FBXHeaderExtension";W=12},
  [pscustomobject]@{C="FBX_SCENE_MODEL";N="Deformer";P="Deformer";W=2},
  [pscustomobject]@{C="FBX_SCENE_MODEL";N="Cluster";P="Cluster";W=3},

  [pscustomobject]@{C="GLTF_GLB";N="glTF_magic";P="glTF";W=15},
  [pscustomobject]@{C="GLTF_GLB";N="skins";P="skins";W=6},
  [pscustomobject]@{C="GLTF_GLB";N="joints";P="joints";W=5},
  [pscustomobject]@{C="GLTF_GLB";N="WEIGHTS_0";P="WEIGHTS_0";W=8},
  [pscustomobject]@{C="GLTF_GLB";N="JOINTS_0";P="JOINTS_0";W=8},

  [pscustomobject]@{C="COLLADA";N="COLLADA";P="<COLLADA";W=20},
  [pscustomobject]@{C="COLLADA";N="controller";P="<controller";W=6},
  [pscustomobject]@{C="COLLADA";N="vertex_weights";P="<vertex_weights";W=10},
  [pscustomobject]@{C="COLLADA";N="visual_scene";P="<visual_scene";W=5},

  [pscustomobject]@{C="PMX_MMD";N="PMX";P="PMX ";W=20},
  [pscustomobject]@{C="PMX_MMD";N="PMD";P="Pmd";W=15},

  [pscustomobject]@{C="GENERIC_RIG";N="Bone";P="Bone";W=2},
  [pscustomobject]@{C="GENERIC_RIG";N="Weight";P="Weight";W=2},
  [pscustomobject]@{C="GENERIC_RIG";N="Skin";P="Skin";W=2},
  [pscustomobject]@{C="GENERIC_RIG";N="Skeleton";P="Skeleton";W=3},
  [pscustomobject]@{C="GENERIC_RIG";N="Joint";P="Joint";W=2},
  [pscustomobject]@{C="GENERIC_RIG";N="Morph";P="Morph";W=2},
  [pscustomobject]@{C="GENERIC_RIG";N="Shape";P="Shape";W=1}
)

$hits=foreach($m in $markers){
  $a=CountText $latin $m.P
  $u=CountText $utf16 $m.P
  $t=$a+$u
  [pscustomobject]@{
    category=$m.C;marker=$m.N;ascii_count=$a;utf16_count=$u;
    total_count=$t;evidence_weight=$m.W;
    evidence_score=$(if($t -gt 0){$m.W}else{0})
  }
}
$hits|Export-Csv (Join-Path $Out "SIGNATURE_HITS.tsv") -Delimiter ([char]9) -NoTypeInformation -Encoding UTF8

$cats=@("ENGINE_ASSET_PACKAGE","FBX_SCENE_MODEL","GLTF_GLB","COLLADA","PMX_MMD","GENERIC_RIG")
$sim=foreach($c in $cats){
  $all=@($hits|Where-Object category -eq $c)
  $hit=@($all|Where-Object total_count -gt 0)
  $s=($hit|Measure-Object evidence_score -Sum).Sum
  $mx=($all|Measure-Object evidence_weight -Sum).Sum
  if($null -eq $s){$s=0};if(-not $mx){$mx=1}
  [pscustomobject]@{
    category=$c;raw_score=$s;possible_score=$mx;
    evidence_percent=[Math]::Round(100.0*$s/$mx,2);
    markers_hit=$hit.Count;markers_total=$all.Count
  }
}
$sim|Sort-Object evidence_percent -Descending|Export-Csv (Join-Path $Out "SIMILARITY_EVIDENCE.tsv") -Delimiter ([char]9) -NoTypeInformation -Encoding UTF8

$teacher=@(59,4,6578,10934,13691,17680,10567,17944)
$fps=foreach($v in $teacher){
  $raw=[BitConverter]::GetBytes([int]$v)
  $needle=[Text.Encoding]::GetEncoding(28591).GetString($raw)
  [pscustomobject]@{
    value=$v;
    little_endian_hex=(($raw|ForEach-Object{$_.ToString("X2")}) -join " ");
    occurrences=(CountText $latin $needle);
    note="Fingerprint only; not semantic proof"
  }
}
$fps|Export-Csv (Join-Path $Out "TEACHER_FINGERPRINTS.tsv") -Delimiter ([char]9) -NoTypeInformation -Encoding UTF8

$toolOut=Join-Path $Out "OPTIONAL_TOOL_RESULTS"
New-Item -ItemType Directory -Path $toolOut -Force|Out-Null
function RunOptional($names,$arguments,$name){
  $cmd=$null
  foreach($n in $names){$x=Get-Command $n -ErrorAction SilentlyContinue;if($x){$cmd=$x;break}}
  $dest=Join-Path $toolOut $name
  if(-not $cmd){"NOT INSTALLED"|Set-Content $dest -Encoding UTF8;return}
  try{& $cmd.Source @arguments 2>&1|Out-File $dest -Encoding UTF8}
  catch{"ERROR=$($_.Exception.Message)"|Set-Content $dest -Encoding UTF8}
}
RunOptional @("trid.exe","trid") @($InputPath) "TRID.txt"
RunOptional @("7z.exe","7zz.exe","7z","7zz") @("l",$InputPath) "7ZIP_LIST.txt"
RunOptional @("file.exe","file") @("-b",$InputPath) "FILE_COMMAND.txt"
RunOptional @("exiftool.exe","exiftool") @($InputPath) "EXIFTOOL.txt"
RunOptional @("binwalk.exe","binwalk") @("-B",$InputPath) "BINWALK_SIGNATURE.txt"
RunOptional @("binwalk.exe","binwalk") @("-E",$InputPath) "BINWALK_ENTROPY.txt"

$summary=@()
$summary+="CSMC COMBINED STATIC SCAN V1"
$summary+="============================"
$summary+=""
$summary+="input=$InputPath"
$summary+="bytes=$($fi.Length)"
$summary+="sha256=$sha"
$summary+=""
$summary+="STRUCTURAL SIMILARITY EVIDENCE"
$summary+="------------------------------"
foreach($x in ($sim|Sort-Object evidence_percent -Descending)){
  $summary+=("{0,-24} score={1,6}% markers={2}/{3}" -f $x.category,$x.evidence_percent,$x.markers_hit,$x.markers_total)
}
$summary+=""
$summary+="Heuristic evidence only; not format identification."
$summary+="semantic_promotion=false"
$summary|Set-Content (Join-Path $Out "SUMMARY.txt") -Encoding UTF8

Get-Content (Join-Path $Out "SUMMARY.txt")
Start-Process explorer.exe -ArgumentList ('"'+$Out+'"')
