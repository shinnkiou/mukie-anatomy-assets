param(
  [string]$ExpectedGuid='19c1747bf2b84da197b9ead412256c5b',
  [switch]$SafeMode
)
$ErrorActionPreference='Stop'
$ToolVersion='0.5.0'
function Q([string]$s){if($null-eq$s){'""'}else{'"'+($s-replace'"','""')+'"'}}
function New-Root{
  $c=@()
  if($env:USERPROFILE){$d=Join-Path $env:USERPROFILE 'Desktop';if(Test-Path $d){$c+=Join-Path $d 'BP3D_ModelerObserver_Captures'}}
  if($env:TEMP){$c+=Join-Path $env:TEMP 'BP3D_ModelerObserver_Captures'}
  foreach($p in $c){try{New-Item -ItemType Directory -Force -Path $p|Out-Null;return $p}catch{}}
  throw 'No writable capture folder.'
}
function ProcPath($p){try{$p.MainModule.FileName}catch{''}}
function Score($p){
  if($null-eq$p-or$p.Id-eq$PID){return -9999}
  $n=$p.ProcessName;$t='';try{$t=$p.MainWindowTitle}catch{};$x=ProcPath $p
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
$Dir=Join-Path $Root ('CAPTURE_'+$Stamp+'_V05');New-Item -ItemType Directory -Force -Path $Dir|Out-Null
$Log=Join-Path $Dir 'observer_v05.log.txt'
function Log($e,$d){((Get-Date).ToString('o')+','+(Q $e)+','+(Q $d))|Add-Content $Log -Encoding UTF8}
"Time,Event,Detail"|Set-Content $Log -Encoding UTF8
Log START "version=$ToolVersion expected_guid=$ExpectedGuid safe=$SafeMode"

$code=@"
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
public static class BP3DTargetDumpV05 {
 const uint VM=0x10,QI=0x400,QLI=0x1000,COMMIT=0x1000,NO=1,GUARD=0x100;
 [StructLayout(LayoutKind.Sequential)] public struct MBI{public IntPtr BaseAddress,AllocationBase;public uint AllocationProtect;public ushort PartitionId;public UIntPtr RegionSize;public uint State,Protect,Type;}
 public class Cand{public ulong BlobStart,MagicAddress,HeaderBytes,Stored,Logical,Total;public uint Version;public string Guid,Kind;public uint Protect,Type;}
 public class SearchResult{public Cand[] Candidates;public ulong Planned,Attempted,Read;public int Regions,Failures;public double Seconds;public string Reason;}
 public class DumpResult{public ulong Planned,Written;public int Failures;public double Seconds;public string Reason,Path,Sha256;}
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr OpenProcess(uint a,bool b,int p);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
 [DllImport("kernel32.dll",SetLastError=true)] static extern UIntPtr VirtualQueryEx(IntPtr h,IntPtr a,out MBI m,UIntPtr s);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool ReadProcessMemory(IntPtr h,IntPtr a,byte[] b,UIntPtr s,out UIntPtr n);
 static bool R(MBI m){return m.State==COMMIT&&(m.Protect&GUARD)==0&&(m.Protect&NO)==0;}
 static uint U32(byte[] b,int o){return BitConverter.ToUInt32(b,o);}
 static int Find(byte[] h,int n,byte[] x,int s){for(int i=s;i<=n-x.Length;i++){bool ok=true;for(int j=0;j<x.Length;j++)if(h[i+j]!=x[j]){ok=false;break;}if(ok)return i;}return -1;}
 static bool ReadAt(IntPtr hp,ulong a,byte[] b,int n){UIntPtr g;return ReadProcessMemory(hp,new IntPtr(unchecked((long)a)),b,new UIntPtr((uint)n),out g)&&g.ToUInt64()==(ulong)n;}
 static string Hex(byte[] b,int o,int n){var s=new StringBuilder(n*2);for(int i=0;i<n;i++)s.Append(b[o+i].ToString("x2"));return s.ToString();}
 static List<MBI> Plan(IntPtr hp,ulong max,out ulong total){
   var z=new List<MBI>();total=0;ulong a=0;int ms=Marshal.SizeOf(typeof(MBI));
   while(a<0x00007FFFFFF00000UL&&total<max){MBI m;var q=VirtualQueryEx(hp,new IntPtr(unchecked((long)a)),out m,new UIntPtr((uint)ms));if(q==UIntPtr.Zero){a+=0x10000;continue;}
    ulong b=unchecked((ulong)m.BaseAddress.ToInt64()),rs=m.RegionSize.ToUInt64(),nx=b+rs;if(rs==0||nx<=a){a+=0x10000;continue;}
    if(R(m)){ulong take=Math.Min(rs,max-total);if(take>0){m.RegionSize=new UIntPtr(take);z.Add(m);total+=take;}}a=nx;}
   return z;
 }
 static void P(string tag,ulong a,ulong t,ulong good,int hits,int fail,Stopwatch sw,bool end){
   if(t==0)t=1;int pct=(int)Math.Min(100UL,a*100UL/t);double rate=(good/1048576.0)/Math.Max(.001,sw.Elapsed.TotalSeconds);
   string s=String.Format("\r[{0}] {1,3}%  {2,7:F1}/{3:F1} MiB  {4,6:F1} MiB/s  hits={5} fail={6}",tag,pct,a/1048576.0,t/1048576.0,rate,hits,fail);
   Console.Write(s.PadRight(112));if(end)Console.WriteLine();
 }
 static Cand Parse(IntPtr hp,ulong magic,string expected,uint prot,uint type){
   if(magic<4)return null;ulong start=magic-4;byte[] h=new byte[128];if(!ReadAt(hp,start,h,h.Length))return null;
   if(U32(h,0)!=20)return null;byte[] mg=Encoding.ASCII.GetBytes("CLIP_STUDIO_3D_DATA2");for(int i=0;i<20;i++)if(h[4+i]!=mg[i])return null;
   int o=24;if(o+4>h.Length)return null;uint kl=U32(h,o);o+=4;if(kl<1||kl>32||o+kl+28>h.Length)return null;
   string kind=Encoding.ASCII.GetString(h,o,(int)kl);o+=(int)kl;if(kind!="character")return null;
   string guid=Hex(h,o,16);o+=16;if(!String.IsNullOrEmpty(expected)&&!guid.Equals(expected,StringComparison.OrdinalIgnoreCase))return null;
   uint ver=U32(h,o),logical=U32(h,o+4),stored=U32(h,o+8);o+=12;
   if(ver>100||stored<1024||stored>1073741824U)return null;
   return new Cand{BlobStart=start,MagicAddress=magic,HeaderBytes=(ulong)o,Stored=stored,Logical=logical,Total=(ulong)o+stored,Version=ver,Guid=guid,Kind=kind,Protect=prot,Type=type};
 }
 public static SearchResult Search(int pid,string expected,ulong max,int timeout){
   var r=new SearchResult();var outp=new List<Cand>();r.Reason="not_started";IntPtr hp=OpenProcess(VM|QI,false,pid);if(hp==IntPtr.Zero)hp=OpenProcess(VM|QLI,false,pid);if(hp==IntPtr.Zero){r.Candidates=outp.ToArray();r.Reason="open_failed";return r;}
   var sw=Stopwatch.StartNew();try{ulong planned;var regs=Plan(hp,max,out planned);r.Planned=planned;r.Regions=regs.Count;byte[] pat=Encoding.ASCII.GetBytes("CLIP_STUDIO_3D_DATA2"),buf=new byte[1024*1024];ulong attempted=0,good=0;int fail=0,last=-1;
    Console.WriteLine(String.Format("[B] Search plan {0:F1} MiB / {1} regions",planned/1048576.0,regs.Count));
    foreach(var m in regs){ulong b=unchecked((ulong)m.BaseAddress.ToInt64()),sz=m.RegionSize.ToUInt64(),off=0;while(off<sz){
      if(timeout>0&&sw.Elapsed.TotalSeconds>=timeout){r.Reason="timeout";goto done;}int want=(int)Math.Min((ulong)buf.Length,sz-off);UIntPtr g;bool ok=ReadProcessMemory(hp,new IntPtr(unchecked((long)(b+off))),buf,new UIntPtr((uint)want),out g);int n=ok?(int)Math.Min((ulong)want,g.ToUInt64()):0;attempted+=(ulong)want;
      if(n>0){good+=(ulong)n;int p=0,c=0;while(c<16){int f=Find(buf,n,pat,p);if(f<0)break;var ca=Parse(hp,b+off+(ulong)f,expected,m.Protect,m.Type);if(ca!=null)outp.Add(ca);p=f+pat.Length;c++;}}else fail++;
      int pct=planned==0?100:(int)Math.Min(100UL,attempted*100UL/planned);if(pct!=last){P("B-search",attempted,planned,good,outp.Count,fail,sw,false);last=pct;}off+=(ulong)want;}}
    r.Reason="complete";
   done:r.Attempted=attempted;r.Read=good;r.Failures=fail;r.Candidates=outp.ToArray();r.Seconds=sw.Elapsed.TotalSeconds;P("B-search",attempted,planned,good,outp.Count,fail,sw,true);return r;
   }finally{sw.Stop();CloseHandle(hp);}
 }
 public static DumpResult Dump(int pid,Cand c,string path,int timeout){
   var r=new DumpResult();r.Planned=c.Total;r.Path=path;r.Reason="not_started";IntPtr hp=OpenProcess(VM|QI,false,pid);if(hp==IntPtr.Zero)hp=OpenProcess(VM|QLI,false,pid);if(hp==IntPtr.Zero){r.Reason="open_failed";return r;}
   var sw=Stopwatch.StartNew();ulong pos=0;int fail=0;try{using(var fs=new FileStream(path,FileMode.Create,FileAccess.Write,FileShare.None)){byte[] buf=new byte[1024*1024];while(pos<c.Total){
     if(timeout>0&&sw.Elapsed.TotalSeconds>=timeout){r.Reason="timeout";break;}ulong a=c.BlobStart+pos;MBI m;int ms=Marshal.SizeOf(typeof(MBI));if(VirtualQueryEx(hp,new IntPtr(unchecked((long)a)),out m,new UIntPtr((uint)ms))==UIntPtr.Zero||!R(m)){r.Reason="unreadable_region";fail++;break;}
     ulong rb=unchecked((ulong)m.BaseAddress.ToInt64()),re=rb+m.RegionSize.ToUInt64();ulong room=re>a?re-a:0;if(room==0){r.Reason="zero_room";fail++;break;}int want=(int)Math.Min((ulong)buf.Length,Math.Min(c.Total-pos,room));UIntPtr g;bool ok=ReadProcessMemory(hp,new IntPtr(unchecked((long)a)),buf,new UIntPtr((uint)want),out g);int n=ok?(int)Math.Min((ulong)want,g.ToUInt64()):0;if(n<=0){r.Reason="read_failed";fail++;break;}fs.Write(buf,0,n);pos+=(ulong)n;P("B-dump",pos,c.Total,pos,0,fail,sw,false);
   }}if(pos==c.Total)r.Reason="complete";r.Written=pos;r.Failures=fail;r.Seconds=sw.Elapsed.TotalSeconds;P("B-dump",pos,c.Total,pos,0,fail,sw,true);
    if(File.Exists(path)){using(var sha=SHA256.Create())using(var f=File.OpenRead(path)){r.Sha256=BitConverter.ToString(sha.ComputeHash(f)).Replace("-","").ToLowerInvariant();}}
    return r;
   }finally{sw.Stop();CloseHandle(hp);}
 }
}
"@
$Interop=$false
if(-not$SafeMode){try{Add-Type -TypeDefinition $code -Language CSharp -ErrorAction Stop;$Interop=$true;Log INTEROP_READY 'Targeted reader compiled.'}catch{Log INTEROP_FAILED $_.Exception.ToString()}}
Write-Host '';Write-Host 'BP3D MODELER OBSERVER v0.5' -ForegroundColor Cyan
Write-Host 'Targeted runtime character-blob capture / read-only.'
Write-Host ('Output: '+$Dir);Write-Host ('Expected GUID: '+$ExpectedGuid)
if($SafeMode){Write-Host 'SAFE MODE: memory capture disabled.' -ForegroundColor Yellow}
Write-Host 'Waiting for CLIP STUDIO MODELER...'
$p=$null
while($null-eq$p){$p=Find-Modeler;if($null-eq$p){Start-Sleep -Milliseconds 500}}
$pp=ProcPath $p;$sc=Score $p
Write-Host ('Attached: '+$p.ProcessName+' PID='+$p.Id) -ForegroundColor Green
Write-Host ('  EXE: '+$pp);Write-Host ('  Score: '+$sc)
Log ATTACH "pid=$($p.Id) name=$($p.ProcessName) score=$sc path=$pp"
Write-Host '';Write-Host 'Keys: B=targeted character blob capture  Q=finish' -ForegroundColor DarkCyan
$last=@();$done=$false
while(-not$done){
  $p=Get-Process -Id $p.Id -ErrorAction SilentlyContinue;if($null-eq$p){Log TARGET_EXIT 'MODELER exited';break}
  if([Console]::KeyAvailable){$k=[Console]::ReadKey($true).KeyChar.ToString()
    if($k-match'[qQ]'){$done=$true;Log USER_MARK FINISH}
    elseif($k-match'[bB]'){
      if(-not$Interop){Write-Host 'Memory capture unavailable.' -ForegroundColor Yellow;continue}
      Log BLOB_SEARCH_START "pid=$($p.Id)"
      $s=[BP3DTargetDumpV05]::Search($p.Id,$ExpectedGuid,[UInt64](2048MB),180);$last=@($s.Candidates)
      $cand=@();$i=0
      foreach($c in $last){$i++;$cand+=[ordered]@{index=$i;blob_start=('0x{0:X}'-f$c.BlobStart);magic_address=('0x{0:X}'-f$c.MagicAddress);guid=$c.Guid;kind=$c.Kind;version=$c.Version;logical=$c.Logical;stored=$c.Stored;header_bytes=$c.HeaderBytes;total=$c.Total;protect=('0x{0:X}'-f$c.Protect);type=('0x{0:X}'-f$c.Type)}}
      $meta=[ordered]@{tool_version=$ToolVersion;pid=$p.Id;process=$p.ProcessName;exe=(ProcPath $p);expected_guid=$ExpectedGuid;search_reason=$s.Reason;search_seconds=$s.Seconds;search_planned=$s.Planned;search_attempted=$s.Attempted;search_read=$s.Read;search_failures=$s.Failures;candidates=$cand}
      $meta|ConvertTo-Json -Depth 6|Set-Content (Join-Path $Dir 'runtime_character_candidates.json') -Encoding UTF8
      Log BLOB_SEARCH_DONE "reason=$($s.Reason) candidates=$($last.Count) seconds=$([math]::Round($s.Seconds,3))"
      if($last.Count-eq0){Write-Host '[B] No validated character candidate found.' -ForegroundColor Yellow;continue}
      Write-Host ('[B] Validated candidates: '+$last.Count) -ForegroundColor Green
      $c=$last[0];$out=Join-Path $Dir ('runtime_character_0x{0:X}.bin'-f$c.BlobStart)
      Write-Host ('[B] Dumping candidate #1: '+$c.Total+' bytes') -ForegroundColor Cyan
      $d=[BP3DTargetDumpV05]::Dump($p.Id,$c,$out,180)
      $dm=[ordered]@{reason=$d.Reason;planned=$d.Planned;written=$d.Written;failures=$d.Failures;seconds=$d.Seconds;sha256=$d.Sha256;path=[IO.Path]::GetFileName($d.Path)}
      $dm|ConvertTo-Json|Set-Content (Join-Path $Dir 'runtime_character_dump.json') -Encoding UTF8
      Log BLOB_DUMP_DONE "reason=$($d.Reason) written=$($d.Written) sha256=$($d.Sha256)"
      if($d.Reason-eq'complete'){Write-Host ('[B] COMPLETE 100% SHA-256 '+$d.Sha256) -ForegroundColor Green}else{Write-Host ('[B] PARTIAL reason='+$d.Reason) -ForegroundColor Yellow}
      Write-Host 'Observer is idle again. Press Q to package output.' -ForegroundColor DarkCyan
    }
  }
  Start-Sleep -Milliseconds 200
}
$manifest=[ordered]@{tool='BP3D Modeler Observer';version=$ToolVersion;expected_guid=$ExpectedGuid;read_only=$true;target_pid=if($p){$p.Id}else{0};target_executable=if($p){ProcPath $p}else{''};end=(Get-Date).ToString('o')}
$manifest|ConvertTo-Json|Set-Content (Join-Path $Dir 'capture_manifest.json') -Encoding UTF8
$zip=$Dir+'.zip';try{Compress-Archive -Path (Join-Path $Dir '*') -DestinationPath $zip -Force;Write-Host ('UPLOAD THIS ZIP: '+$zip) -ForegroundColor Green}catch{Write-Host ('ZIP failed; upload folder: '+$Dir) -ForegroundColor Yellow}
Write-Host '';Write-Host 'Press Enter to close.';try{[Console]::ReadLine()|Out-Null}catch{}
