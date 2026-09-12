param(
  [string]$ExpectedGuid='19c1747bf2b84b1ba9fc6d63bd173b920',
  [UInt64]$SavedLogical=77081794,
  [UInt64]$SavedStored=77081808,
  [int]$MaxScanMiB=4096,
  [int]$SearchTimeoutSec=240,
  [int]$DumpTimeoutSec=180,
  [switch]$SafeMode
)

# NOTE: ExpectedGuid is replaced below at startup if the historical typo-safe default is detected.
if($ExpectedGuid -eq '19c1747bf2b84b1ba9fc6d63bd173b920'){$ExpectedGuid='19c1747bf2b84da197b9ead412256c5b'}
$ErrorActionPreference='Stop'
$ToolVersion='P4.1.0-worker'

function Q([string]$s){if($null-eq$s){'""'}else{'"'+($s-replace'"','""')+'"'}}
function New-Root{
  $c=@()
  if($env:USERPROFILE){$d=Join-Path $env:USERPROFILE 'Desktop';if(Test-Path $d){$c+=Join-Path $d 'BP3D_ModelerObserver_P4_1_Captures'}}
  if($env:TEMP){$c+=Join-Path $env:TEMP 'BP3D_ModelerObserver_P4_1_Captures'}
  foreach($p in $c){try{New-Item -ItemType Directory -Force -Path $p|Out-Null;return $p}catch{}}
  throw 'No writable capture folder.'
}
function ProcPath($p){try{$p.MainModule.FileName}catch{''}}
function ProcTitle($p){try{$p.MainWindowTitle}catch{''}}
function ProcStart($p){try{$p.StartTime.ToString('o')}catch{''}}
function Score($p){
  if($null-eq$p-or$p.Id-eq$PID){return -9999}
  $n=$p.ProcessName;$t=ProcTitle $p;$x=ProcPath $p
  if($n-match'(?i)^BP3D_ModelerObserver|^(powershell|pwsh|cmd|conhost|WindowsTerminal|OpenConsole)$'){return -9999}
  $s=0
  if($t-match'(?i)CLIP STUDIO MODELER'){$s+=200}
  if($n-match'(?i)^CLIP.?Studio.?Modeler$'){$s+=160}elseif($n-match'(?i)clip.*modeler|modeler.*clip'){$s+=120}
  if($x-match'(?i)CELSYS'){$s+=80};if($x-match'(?i)CLIP.*Modeler|Modeler.*CLIP'){$s+=80}
  try{$v=$p.MainModule.FileVersionInfo;if($v.CompanyName-match'(?i)CELSYS'){$s+=80};if($v.ProductName-match'(?i)CLIP STUDIO MODELER'){$s+=120}}catch{}
  return $s
}
function Find-Modeler{
  $best=$null;$bs=-9999
  foreach($p in Get-Process -ErrorAction SilentlyContinue){$s=Score $p;if($s-gt$bs){$best=$p;$bs=$s}}
  if($bs-ge100){return $best};return $null
}

$Root=New-Root;$Stamp=Get-Date -Format yyyyMMdd_HHmmss
$Dir=Join-Path $Root ('CAPTURE_'+$Stamp+'_P4_1');New-Item -ItemType Directory -Force -Path $Dir|Out-Null
$Log=Join-Path $Dir 'observer_p4_1.log.txt'
function Log($e,$d){((Get-Date).ToString('o')+','+(Q $e)+','+(Q $d))|Add-Content $Log -Encoding UTF8}
"Time,Event,Detail"|Set-Content $Log -Encoding UTF8
Log START "version=$ToolVersion expected_guid=$ExpectedGuid saved_logical=$SavedLogical saved_stored=$SavedStored safe=$SafeMode max_scan_mib=$MaxScanMiB auto_run=true worker_fixed_sidecar=true"

$code=@"
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
public static class BP3DTargetDumpP41 {
 const uint VM=0x10,QI=0x400,QLI=0x1000,COMMIT=0x1000,NO=1,GUARD=0x100;
 const uint MEM_PRIVATE=0x20000,MEM_MAPPED=0x40000,MEM_IMAGE=0x1000000;
 const int OVERLAP=64;
 [StructLayout(LayoutKind.Sequential)] public struct MBI{public IntPtr BaseAddress,AllocationBase;public uint AllocationProtect;public ushort PartitionId;public UIntPtr RegionSize;public uint State,Protect,Type;}
 public class Hit{
   public ulong MagicAddress,BlobStart; public uint Protect,Type,Version; public string TypeName,Kind,Guid,RejectReason;
   public ulong Logical,Stored,HeaderBytes,Total; public long StoredMinusAlign8Logical;
   public bool FullHeader,ExactGuid,KindCharacter,Version2,SaneSizes,InvariantOk,Accepted;
 }
 public class SearchResult{
   public Hit[] Hits; public ulong Planned,Attempted,Read; public int Regions,Failures; public double Seconds; public string Reason;
   public int PrivateRegions,MappedRegions,ImageRegions,OtherRegions; public ulong PrivateBytes,MappedBytes,ImageBytes,OtherBytes;
 }
 public class DumpResult{public ulong Planned,Written;public int Failures;public double Seconds;public string Reason,Path,Sha256;}
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr OpenProcess(uint a,bool b,int p);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
 [DllImport("kernel32.dll",SetLastError=true)] static extern UIntPtr VirtualQueryEx(IntPtr h,IntPtr a,out MBI m,UIntPtr s);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool ReadProcessMemory(IntPtr h,IntPtr a,byte[] b,UIntPtr s,out UIntPtr n);
 static bool R(MBI m){return m.State==COMMIT&&(m.Protect&GUARD)==0&&(m.Protect&NO)==0;}
 static bool RP(MBI m){return R(m)&&m.Type==MEM_PRIVATE;}
 static uint U32(byte[] b,int o){return BitConverter.ToUInt32(b,o);}
 static string Hex(byte[] b,int o,int n){var s=new StringBuilder(n*2);for(int i=0;i<n;i++)s.Append(b[o+i].ToString("x2"));return s.ToString();}
 static ulong Align8(ulong n){return ((n+7UL)/8UL)*8UL;}
 static string TN(uint t){if(t==MEM_PRIVATE)return "MEM_PRIVATE";if(t==MEM_MAPPED)return "MEM_MAPPED";if(t==MEM_IMAGE)return "MEM_IMAGE";return "OTHER_0x"+t.ToString("X");}
 static int Find(byte[] h,int n,byte[] x,int s){for(int i=s;i<=n-x.Length;i++){bool ok=true;for(int j=0;j<x.Length;j++)if(h[i+j]!=x[j]){ok=false;break;}if(ok)return i;}return -1;}
 static bool ReadAt(IntPtr hp,ulong a,byte[] b,int n){UIntPtr g;return ReadProcessMemory(hp,new IntPtr(unchecked((long)a)),b,new UIntPtr((uint)n),out g)&&g.ToUInt64()==(ulong)n;}
 static List<MBI> Plan(IntPtr hp,ulong max,out ulong total,SearchResult stat){
   var z=new List<MBI>();total=0;ulong a=0;int ms=Marshal.SizeOf(typeof(MBI));
   while(a<0x00007FFFFFF00000UL&&total<max){MBI m;var q=VirtualQueryEx(hp,new IntPtr(unchecked((long)a)),out m,new UIntPtr((uint)ms));if(q==UIntPtr.Zero){a+=0x10000;continue;}
     ulong b=unchecked((ulong)m.BaseAddress.ToInt64()),rs=m.RegionSize.ToUInt64(),nx=b+rs;if(rs==0||nx<=a){a+=0x10000;continue;}
     if(R(m)){ulong take=Math.Min(rs,max-total);if(take>0){m.RegionSize=new UIntPtr(take);z.Add(m);total+=take;
       if(m.Type==MEM_PRIVATE){stat.PrivateRegions++;stat.PrivateBytes+=take;}else if(m.Type==MEM_MAPPED){stat.MappedRegions++;stat.MappedBytes+=take;}else if(m.Type==MEM_IMAGE){stat.ImageRegions++;stat.ImageBytes+=take;}else{stat.OtherRegions++;stat.OtherBytes+=take;}
     }}a=nx;}
   return z;
 }
 static Hit Parse(IntPtr hp,ulong magic,string expected,uint prot,uint type){
   var h=new Hit{MagicAddress=magic,BlobStart=magic>=4?magic-4:0,Protect=prot,Type=type,TypeName=TN(type),RejectReason="unparsed"};
   if(magic<4){h.RejectReason="magic_before_lp_prefix";return h;}
   byte[] b=new byte[160];if(!ReadAt(hp,magic-4,b,b.Length)){h.RejectReason="full_header_read_failed";return h;}
   if(U32(b,0)!=20){h.RejectReason="lp_magic_length_not_20";return h;}
   byte[] mg=Encoding.ASCII.GetBytes("CLIP_STUDIO_3D_DATA2");for(int i=0;i<20;i++)if(b[4+i]!=mg[i]){h.RejectReason="magic_mismatch_after_prefix";return h;}
   int o=24;uint kl=U32(b,o);o+=4;if(kl<1||kl>32||o+kl+28>b.Length){h.RejectReason="kind_length_invalid";return h;}
   h.Kind=Encoding.ASCII.GetString(b,o,(int)kl);o+=(int)kl;h.Guid=Hex(b,o,16);o+=16;h.Version=U32(b,o);h.Logical=U32(b,o+4);h.Stored=U32(b,o+8);o+=12;h.HeaderBytes=(ulong)o;h.Total=h.HeaderBytes+h.Stored;h.FullHeader=true;
   h.ExactGuid=!String.IsNullOrEmpty(expected)&&h.Guid.Equals(expected,StringComparison.OrdinalIgnoreCase);
   h.KindCharacter=h.Kind=="character";h.Version2=h.Version==2;
   h.SaneSizes=h.Logical>=1024&&h.Stored>=1024&&h.Stored<=1073741824UL&&h.Stored>=h.Logical;
   if(h.SaneSizes){h.StoredMinusAlign8Logical=(long)(h.Stored-Align8(h.Logical));h.InvariantOk=h.StoredMinusAlign8Logical==8;}else{h.StoredMinusAlign8Logical=long.MinValue;}
   h.Accepted=type==MEM_PRIVATE&&h.FullHeader&&h.KindCharacter&&h.ExactGuid&&h.Version2&&h.SaneSizes&&h.InvariantOk;
   if(h.Accepted)h.RejectReason="ACCEPTED";
   else if(type!=MEM_PRIVATE)h.RejectReason="not_mem_private";
   else if(!h.KindCharacter)h.RejectReason="kind_not_character";
   else if(!h.ExactGuid)h.RejectReason="guid_mismatch";
   else if(!h.Version2)h.RejectReason="version_not_2";
   else if(!h.SaneSizes)h.RejectReason="size_sanity_failed";
   else if(!h.InvariantOk)h.RejectReason="stored_alignment_invariant_failed";
   else h.RejectReason="rejected";
   return h;
 }
 static void P(string tag,ulong a,ulong t,ulong good,int hits,int fail,Stopwatch sw,bool end){if(t==0)t=1;int pct=(int)Math.Min(100UL,a*100UL/t);double rate=(good/1048576.0)/Math.Max(.001,sw.Elapsed.TotalSeconds);string s=String.Format("\r[{0}] {1,3}% {2,8:F1}/{3:F1} MiB {4,6:F1} MiB/s magic={5} fail={6}",tag,pct,a/1048576.0,t/1048576.0,rate,hits,fail);Console.Write(s.PadRight(118));if(end)Console.WriteLine();}
 public static SearchResult Search(int pid,string expected,ulong max,int timeout){
   var r=new SearchResult();var hits=new List<Hit>();r.Reason="not_started";IntPtr hp=OpenProcess(VM|QI,false,pid);if(hp==IntPtr.Zero)hp=OpenProcess(VM|QLI,false,pid);if(hp==IntPtr.Zero){r.Hits=hits.ToArray();r.Reason="open_failed";return r;}
   var sw=Stopwatch.StartNew();try{ulong planned;var regs=Plan(hp,max,out planned,r);r.Planned=planned;r.Regions=regs.Count;byte[] pat=Encoding.ASCII.GetBytes("CLIP_STUDIO_3D_DATA2"),buf=new byte[1024*1024+OVERLAP];ulong attempted=0,good=0;int fail=0,last=-1;
     Console.WriteLine(String.Format("[P4.1] all-readable search plan {0:F1} MiB / {1} regions",planned/1048576.0,regs.Count));
     foreach(var m in regs){ulong rb=unchecked((ulong)m.BaseAddress.ToInt64()),sz=m.RegionSize.ToUInt64(),off=0;int carry=0;
       while(off<sz){if(timeout>0&&sw.Elapsed.TotalSeconds>=timeout){r.Reason="timeout";goto done;}int want=(int)Math.Min(1024UL*1024UL,sz-off);UIntPtr g;bool ok=ReadProcessMemory(hp,new IntPtr(unchecked((long)(rb+off))),buf,new UIntPtr((uint)want),out g);int n=ok?(int)Math.Min((ulong)want,g.ToUInt64()):0;attempted+=(ulong)want;
         if(n>0){good+=(ulong)n;int total=carry+n;int pos=0,count=0;while(count<128){int f=Find(buf,total,pat,pos);if(f<0)break;ulong abs=rb+off-(ulong)carry+(ulong)f;hits.Add(Parse(hp,abs,expected,m.Protect,m.Type));pos=f+pat.Length;count++;}
           carry=Math.Min(OVERLAP,total);Buffer.BlockCopy(buf,total-carry,buf,0,carry);
         }else{fail++;carry=0;}
         int pct=planned==0?100:(int)Math.Min(100UL,attempted*100UL/planned);if(pct!=last){P("P4.1-scan",attempted,planned,good,hits.Count,fail,sw,false);last=pct;}off+=(ulong)want;
       }
     }r.Reason="complete";
   done:r.Attempted=attempted;r.Read=good;r.Failures=fail;r.Hits=hits.ToArray();r.Seconds=sw.Elapsed.TotalSeconds;P("P4.1-scan",attempted,planned,good,hits.Count,fail,sw,true);return r;
   }finally{sw.Stop();CloseHandle(hp);}
 }
 public static DumpResult Dump(int pid,Hit c,string path,int timeout){
   var r=new DumpResult{Planned=c.Total,Path=path,Reason="not_started"};if(!c.Accepted){r.Reason="candidate_not_fail_closed_validated";return r;}IntPtr hp=OpenProcess(VM|QI,false,pid);if(hp==IntPtr.Zero)hp=OpenProcess(VM|QLI,false,pid);if(hp==IntPtr.Zero){r.Reason="open_failed";return r;}
   var sw=Stopwatch.StartNew();ulong pos=0;int fail=0;try{using(var fs=new FileStream(path,FileMode.Create,FileAccess.Write,FileShare.None)){byte[] buf=new byte[1024*1024];while(pos<c.Total){if(timeout>0&&sw.Elapsed.TotalSeconds>=timeout){r.Reason="timeout";break;}ulong a=c.BlobStart+pos;MBI m;int ms=Marshal.SizeOf(typeof(MBI));if(VirtualQueryEx(hp,new IntPtr(unchecked((long)a)),out m,new UIntPtr((uint)ms))==UIntPtr.Zero||!RP(m)){r.Reason="non_private_or_unreadable_region";fail++;break;}ulong rb=unchecked((ulong)m.BaseAddress.ToInt64()),re=rb+m.RegionSize.ToUInt64();ulong room=re>a?re-a:0;if(room==0){r.Reason="zero_room";fail++;break;}int want=(int)Math.Min((ulong)buf.Length,Math.Min(c.Total-pos,room));UIntPtr g;bool ok=ReadProcessMemory(hp,new IntPtr(unchecked((long)a)),buf,new UIntPtr((uint)want),out g);int n=ok?(int)Math.Min((ulong)want,g.ToUInt64()):0;if(n<=0){r.Reason="read_failed";fail++;break;}fs.Write(buf,0,n);pos+=(ulong)n;}}
     if(pos==c.Total)r.Reason="complete";r.Written=pos;r.Failures=fail;r.Seconds=sw.Elapsed.TotalSeconds;if(File.Exists(path)){using(var sha=SHA256.Create())using(var f=File.OpenRead(path)){r.Sha256=BitConverter.ToString(sha.ComputeHash(f)).Replace("-","").ToLowerInvariant();}}return r;
   }finally{sw.Stop();CloseHandle(hp);}
 }
}
"@

$Interop=$false
if(-not$SafeMode){try{Add-Type -TypeDefinition $code -Language CSharp -ErrorAction Stop;$Interop=$true;Log INTEROP_READY 'P4.1 all-readable diagnostic reader compiled.'}catch{Log INTEROP_FAILED $_.Exception.ToString()}}
Write-Host ''
Write-Host 'BP3D MODELER OBSERVER P4.1 AUTO / WORKER FIXED SIDECAR' -ForegroundColor Cyan
Write-Host 'Uses an already-running CLIP STUDIO MODELER session when present.'
Write-Host 'Diagnostic scan: all committed readable memory, with 64-byte chunk overlap.'
Write-Host 'Dump gate remains strict: exactly one accepted MEM_PRIVATE character + exact GUID + v2 + invariant.'
Write-Host 'No process memory is modified. No network upload is performed.'
Write-Host ('Output: '+$Dir)
Write-Host ('Expected GUID: '+$ExpectedGuid)
if($SafeMode){Write-Host 'SAFE MODE: memory scan/dump disabled.' -ForegroundColor Yellow}

$p=Find-Modeler
$alreadyRunning=$null-ne$p
if($null-eq$p){
  Write-Host 'MODELER is not currently running. Waiting for an existing session...' -ForegroundColor Yellow
  while($null-eq$p){$p=Find-Modeler;if($null-eq$p){Start-Sleep -Milliseconds 500}}
}
$pp=ProcPath $p;$sc=Score $p;$title=ProcTitle $p;$start=ProcStart $p
Write-Host ('Attached: '+$p.ProcessName+' PID='+$p.Id) -ForegroundColor Green
Write-Host ('  EXE: '+$pp)
Write-Host ('  Existing at observer start: '+$alreadyRunning)
Log ATTACH "pid=$($p.Id) name=$($p.ProcessName) score=$sc path=$pp already_running=$alreadyRunning process_start=$start title=$title"

if(-not$Interop){Write-Host 'Interop unavailable; packaging diagnostics only.' -ForegroundColor Yellow}
elseif(-not$SafeMode){
  Log DIAG_SCAN_START "pid=$($p.Id) all_readable=true overlap=64"
  $s=[BP3DTargetDumpP41]::Search($p.Id,$ExpectedGuid,[UInt64]$MaxScanMiB*1MB,$SearchTimeoutSec)
  $all=@();$accepted=@();$byType=@{};$byReject=@{}
  foreach($h in @($s.Hits)){
    $row=[ordered]@{magic_address=('0x{0:X}'-f$h.MagicAddress);blob_start=('0x{0:X}'-f$h.BlobStart);type=$h.TypeName;type_raw=('0x{0:X}'-f$h.Type);protect=('0x{0:X}'-f$h.Protect);full_header=$h.FullHeader;kind=$h.Kind;guid=$h.Guid;version=$h.Version;logical=$h.Logical;stored=$h.Stored;stored_minus_align8_logical=$h.StoredMinusAlign8Logical;exact_guid=$h.ExactGuid;kind_character=$h.KindCharacter;version_2=$h.Version2;sane_sizes=$h.SaneSizes;invariant_ok=$h.InvariantOk;accepted=$h.Accepted;reject_reason=$h.RejectReason}
    $all+=$row
    if($h.Accepted){$accepted+=$row}
    $tk=$h.TypeName;if(-not$byType.ContainsKey($tk)){$byType[$tk]=0};$byType[$tk]++
    $rk=$h.RejectReason;if(-not$byReject.ContainsKey($rk)){$byReject[$rk]=0};$byReject[$rk]++
  }
  $diag=[ordered]@{tool_version=$ToolVersion;pid=$p.Id;process=$p.ProcessName;exe=$pp;target_already_running=$alreadyRunning;process_start=$start;window_title=$title;expected_guid=$ExpectedGuid;saved_logical=$SavedLogical;saved_stored=$SavedStored;diagnostic_scope='all committed readable memory';chunk_overlap_bytes=64;acceptance_mem_private_required=$true;search_reason=$s.Reason;search_seconds=$s.Seconds;search_planned=$s.Planned;search_attempted=$s.Attempted;search_read=$s.Read;search_failures=$s.Failures;regions=[ordered]@{total=$s.Regions;private=$s.PrivateRegions;mapped=$s.MappedRegions;image=$s.ImageRegions;other=$s.OtherRegions};bytes=[ordered]@{private=$s.PrivateBytes;mapped=$s.MappedBytes;image=$s.ImageBytes;other=$s.OtherBytes};magic_hit_count=@($s.Hits).Count;accepted_count=$accepted.Count;hits_by_type=$byType;reject_reason_counts=$byReject;hits=$all}
  $diag|ConvertTo-Json -Depth 8|Set-Content (Join-Path $Dir 'runtime_memory_diagnostic.json') -Encoding UTF8
  $accepted|ConvertTo-Json -Depth 6|Set-Content (Join-Path $Dir 'accepted_candidates.json') -Encoding UTF8
  Log DIAG_SCAN_DONE "reason=$($s.Reason) magic_hits=$(@($s.Hits).Count) accepted=$($accepted.Count) seconds=$([math]::Round($s.Seconds,3)) failures=$($s.Failures)"
  Write-Host ('[P4.1] magic hits='+@($s.Hits).Count+' accepted='+$accepted.Count+' failures='+$s.Failures) -ForegroundColor Cyan
  if($accepted.Count-eq1){
    $c=@($s.Hits|Where-Object{$_.Accepted})[0]
    $out=Join-Path $Dir ('runtime_character_PRIVATE_0x{0:X}.bin'-f$c.BlobStart)
    Write-Host '[P4.1] Exactly one accepted MEM_PRIVATE candidate. Read-only dump starting.' -ForegroundColor Green
    $d=[BP3DTargetDumpP41]::Dump($p.Id,$c,$out,$DumpTimeoutSec)
    [ordered]@{reason=$d.Reason;planned=$d.Planned;written=$d.Written;failures=$d.Failures;seconds=$d.Seconds;sha256=$d.Sha256;path=[IO.Path]::GetFileName($d.Path);private_payload=$true;automatic_network_upload=$false}|ConvertTo-Json|Set-Content (Join-Path $Dir 'runtime_character_dump.json') -Encoding UTF8
    Log BLOB_DUMP_DONE "reason=$($d.Reason) written=$($d.Written) sha256=$($d.Sha256)"
  }elseif($accepted.Count-gt1){Log BLOB_DUMP_SKIPPED 'ambiguous_accepted_candidate_count';Write-Host '[P4.1] Multiple accepted candidates; no dump.' -ForegroundColor Yellow}
  else{Log BLOB_DUMP_SKIPPED 'no_accepted_candidate';Write-Host '[P4.1] No accepted candidate; diagnostic metadata packaged.' -ForegroundColor Yellow}
}

$manifest=[ordered]@{tool='BP3D Modeler Observer P4.1 AUTO / Worker fixed sidecar';version=$ToolVersion;expected_guid=$ExpectedGuid;read_only=$true;diagnostic_all_readable=$true;chunk_overlap_bytes=64;dump_mem_private_required=$true;full_header_required=$true;stored_alignment_relation_required=8;automatic_network_upload=$false;auto_scan=$true;worker_fixed_sidecar=$true;explorer_launch=$false;target_already_running=$alreadyRunning;contains_private_runtime_payload=([bool](Get-ChildItem -Path $Dir -Filter 'runtime_character_PRIVATE_*.bin' -ErrorAction SilentlyContinue));target_pid=$p.Id;target_executable=$pp;end=(Get-Date).ToString('o')}
$manifest|ConvertTo-Json|Set-Content (Join-Path $Dir 'capture_manifest.json') -Encoding UTF8
$zip=$Dir+'.zip'
try{Compress-Archive -Path (Join-Path $Dir '*') -DestinationPath $zip -Force;Write-Host ('PRIVATE OUTPUT ZIP: '+$zip) -ForegroundColor Green;Log PACKAGE "zip=$zip"}catch{Write-Host ('ZIP failed; keep folder private: '+$Dir) -ForegroundColor Yellow;Log PACKAGE_FAILED $_.Exception.Message;exit 2}
Write-Host 'P4.1 AUTO worker sidecar finished. MODELER was not closed, modified, focused, or reloaded.' -ForegroundColor DarkCyan
