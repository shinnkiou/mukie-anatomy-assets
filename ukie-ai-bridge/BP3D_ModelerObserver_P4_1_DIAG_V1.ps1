param(
  [string]$ExpectedGuid='19c1747bf2b84da197b9ead412256c5b',
  [UInt64]$SavedLogical=77081794,
  [UInt64]$SavedStored=77081808,
  [int]$MaxScanMiB=4096,
  [int]$SearchTimeoutSec=240
)

$ErrorActionPreference='Stop'
$ToolVersion='P4.1.1-diagnose-v1'
$DiagSchema='csmc_observer_diagnose_v1'

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
$Dir=Join-Path $Root ('CAPTURE_'+$Stamp+'_P4_1_DIAG');New-Item -ItemType Directory -Force -Path $Dir|Out-Null
$Log=Join-Path $Dir 'observer_p4_1_diag.log.txt'
function Log($e,$d){((Get-Date).ToString('o')+','+(Q $e)+','+(Q $d))|Add-Content $Log -Encoding UTF8}
"Time,Event,Detail"|Set-Content $Log -Encoding UTF8
Log START "version=$ToolVersion schema=$DiagSchema expected_guid=$ExpectedGuid max_scan_mib=$MaxScanMiB diagnostic_only=true"

$code=@"
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
public static class BP3DDiagnoseV1 {
 const uint VM=0x10,QI=0x400,QLI=0x1000,COMMIT=0x1000,NO=1,GUARD=0x100;
 const uint MEM_PRIVATE=0x20000,MEM_MAPPED=0x40000,MEM_IMAGE=0x1000000;
 const int OVERLAP=64,MAX_FAILURE_DETAILS=64;
 [StructLayout(LayoutKind.Sequential)] public struct MBI{public IntPtr BaseAddress,AllocationBase;public uint AllocationProtect;public ushort PartitionId;public UIntPtr RegionSize;public uint State,Protect,Type;}
 public class Hit{
   public ulong MagicAddress,BlobStart; public uint Protect,Type,Version; public string TypeName,Kind,Guid,RejectReason;
   public ulong Logical,Stored,HeaderBytes,Total; public long StoredMinusAlign8Logical;
   public bool FullHeader,ExactGuid,KindCharacter,Version2,SaneSizes,InvariantOk,Accepted;
 }
 public class ReadFailure{
   public ulong RegionBase,RegionSize,Offset; public uint Protect,Type; public int RequestedBytes,Win32Error; public string TypeName;
 }
 public class SearchResult{
   public Hit[] Hits; public ReadFailure[] FailureDetails; public ulong Planned,Attempted,Read; public int Regions,Failures; public double Seconds; public string Reason;
   public int PrivateRegions,MappedRegions,ImageRegions,OtherRegions; public ulong PrivateBytes,MappedBytes,ImageBytes,OtherBytes; public bool FailureDetailsTruncated;
 }
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr OpenProcess(uint a,bool b,int p);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
 [DllImport("kernel32.dll",SetLastError=true)] static extern UIntPtr VirtualQueryEx(IntPtr h,IntPtr a,out MBI m,UIntPtr s);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool ReadProcessMemory(IntPtr h,IntPtr a,byte[] b,UIntPtr s,out UIntPtr n);
 static bool R(MBI m){return m.State==COMMIT&&(m.Protect&GUARD)==0&&(m.Protect&NO)==0;}
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
 public static SearchResult Search(int pid,string expected,ulong max,int timeout){
   var r=new SearchResult();var hits=new List<Hit>();var failures=new List<ReadFailure>();r.Reason="not_started";IntPtr hp=OpenProcess(VM|QI,false,pid);if(hp==IntPtr.Zero)hp=OpenProcess(VM|QLI,false,pid);if(hp==IntPtr.Zero){r.Hits=hits.ToArray();r.FailureDetails=failures.ToArray();r.Reason="open_failed";return r;}
   var sw=Stopwatch.StartNew();try{ulong planned;var regs=Plan(hp,max,out planned,r);r.Planned=planned;r.Regions=regs.Count;byte[] pat=Encoding.ASCII.GetBytes("CLIP_STUDIO_3D_DATA2"),buf=new byte[1024*1024+OVERLAP];ulong attempted=0,good=0;int fail=0;
     foreach(var m in regs){ulong rb=unchecked((ulong)m.BaseAddress.ToInt64()),sz=m.RegionSize.ToUInt64(),off=0;int carry=0;
       while(off<sz){if(timeout>0&&sw.Elapsed.TotalSeconds>=timeout){r.Reason="timeout";goto done;}int want=(int)Math.Min(1024UL*1024UL,sz-off);UIntPtr g;bool ok=ReadProcessMemory(hp,new IntPtr(unchecked((long)(rb+off))),buf,new UIntPtr((uint)want),out g);int n=ok?(int)Math.Min((ulong)want,g.ToUInt64()):0;attempted+=(ulong)want;
         if(n>0){good+=(ulong)n;int total=carry+n;int pos=0,count=0;while(count<128){int f=Find(buf,total,pat,pos);if(f<0)break;ulong abs=rb+off-(ulong)carry+(ulong)f;hits.Add(Parse(hp,abs,expected,m.Protect,m.Type));pos=f+pat.Length;count++;}carry=Math.Min(OVERLAP,total);Buffer.BlockCopy(buf,total-carry,buf,0,carry);}
         else{fail++;if(failures.Count<MAX_FAILURE_DETAILS){failures.Add(new ReadFailure{RegionBase=rb,RegionSize=sz,Offset=off,Protect=m.Protect,Type=m.Type,TypeName=TN(m.Type),RequestedBytes=want,Win32Error=Marshal.GetLastWin32Error()});}carry=0;}
         off+=(ulong)want;
       }
     }r.Reason="complete";
   done:r.Attempted=attempted;r.Read=good;r.Failures=fail;r.Hits=hits.ToArray();r.FailureDetails=failures.ToArray();r.FailureDetailsTruncated=fail>failures.Count;r.Seconds=sw.Elapsed.TotalSeconds;return r;
   }finally{sw.Stop();CloseHandle(hp);}
 }
}
"@

Add-Type -TypeDefinition $code -Language CSharp -ErrorAction Stop
$p=Find-Modeler
$alreadyRunning=$null-ne$p
if($null-eq$p){throw 'Existing CLIP STUDIO MODELER session not found; diagnose_v1 never launches MODELER.'}
$pp=ProcPath $p;$title=ProcTitle $p;$start=ProcStart $p
Log ATTACH "pid=$($p.Id) path=$pp already_running=$alreadyRunning"
Log DIAG_SCAN_START "pid=$($p.Id) algorithm=P4.1 unchanged counters_only=true"
$s=[BP3DDiagnoseV1]::Search($p.Id,$ExpectedGuid,[UInt64]$MaxScanMiB*1MB,$SearchTimeoutSec)
$hits=@($s.Hits)
$byReject=@{};foreach($h in $hits){$rk=$h.RejectReason;if(-not$byReject.ContainsKey($rk)){$byReject[$rk]=0};$byReject[$rk]++}
$private=@($hits|Where-Object{$_.TypeName-eq'MEM_PRIVATE'})
$kind=@($private|Where-Object{$_.FullHeader-and$_.KindCharacter})
$guid=@($kind|Where-Object{$_.ExactGuid})
$ver=@($guid|Where-Object{$_.Version2})
$sane=@($ver|Where-Object{$_.SaneSizes})
$inv=@($sane|Where-Object{$_.InvariantOk})
$accepted=@($inv|Where-Object{$_.Accepted})
$failRows=@();foreach($f in @($s.FailureDetails)){$failRows += [ordered]@{region_base=('0x{0:X}'-f$f.RegionBase);region_size=$f.RegionSize;offset=$f.Offset;type=$f.TypeName;type_raw=('0x{0:X}'-f$f.Type);protect=('0x{0:X}'-f$f.Protect);requested_bytes=$f.RequestedBytes;win32_error=$f.Win32Error}}
$diag=[ordered]@{
  schema_version=$DiagSchema;tool_version=$ToolVersion;diagnostic_only=$true;payload_dump_allowed=$false;read_only=$true
  pid=$p.Id;process=$p.ProcessName;exe=$pp;target_already_running=$alreadyRunning;process_start=$start;window_title=$title
  expected_guid=$ExpectedGuid;saved_logical=$SavedLogical;saved_stored=$SavedStored
  scan_algorithm='P4.1 unchanged all-readable committed memory scan';search_reason=$s.Reason;search_seconds=$s.Seconds;search_planned=$s.Planned;search_attempted=$s.Attempted;search_read=$s.Read
  regions=[ordered]@{scanned_committed_readable=$s.Regions;readable_mem_private=$s.PrivateRegions;mapped=$s.MappedRegions;image=$s.ImageRegions;other=$s.OtherRegions}
  predicate_pipeline=[ordered]@{prefix_hits=$hits.Count;mem_private_prefix_hits=$private.Count;kind_character=$kind.Count;expected_guid=$guid.Count;version_2=$ver.Count;size_sanity=$sane.Count;stored_align8_logical_eq_8=$inv.Count;accepted=$accepted.Count}
  read_failures=[ordered]@{count=$s.Failures;details_truncated=$s.FailureDetailsTruncated;details=$failRows}
  reject_reason_counts=$byReject
}
$diag|ConvertTo-Json -Depth 9|Set-Content (Join-Path $Dir 'runtime_memory_diagnostic.json') -Encoding UTF8
$manifest=[ordered]@{schema_version='csmc_observer_diagnose_manifest_v1';tool='BP3D Modeler Observer P4.1 diagnose v1';version=$ToolVersion;read_only=$true;diagnostic_only=$true;payload_dump_allowed=$false;automatic_network_upload=$false;target_already_running=$alreadyRunning;modeler_launch_performed=$false;model_load_performed=$false;focus_change_performed=$false;contains_private_runtime_payload=$false;target_pid=$p.Id;target_executable=$pp;end=(Get-Date).ToString('o')}
$manifest|ConvertTo-Json|Set-Content (Join-Path $Dir 'capture_manifest.json') -Encoding UTF8
Log DIAG_SCAN_DONE "reason=$($s.Reason) prefix=$($hits.Count) private=$($private.Count) kind=$($kind.Count) guid=$($guid.Count) version=$($ver.Count) sane=$($sane.Count) invariant=$($inv.Count) accepted=$($accepted.Count) read_failures=$($s.Failures)"
$zip=$Dir+'.zip'
Compress-Archive -Path (Join-Path $Dir '*') -DestinationPath $zip -Force
Log PACKAGE "zip=$zip"
Write-Host ('PRIVATE DIAGNOSTIC ZIP: '+$zip) -ForegroundColor Green
Write-Host 'diagnose_v1 finished. No payload dump, MODELER launch/load/focus, process write, or network upload was performed.' -ForegroundColor DarkCyan
