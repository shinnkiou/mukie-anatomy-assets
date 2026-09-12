import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const FIXED_DRIVE_FOLDER_ID = "1EN2R6DrjsyObR2YpVFFxf1K3wFkMdzwv";
const MAX_ARTIFACT_BYTES = 128 * 1024 * 1024;
const DEVICE_KEY = /^[0-9a-zA-Z_-]{8,128}$/;
const CAPTURE_NAME = /^CAPTURE_\d{8}_\d{6}_P4(?:_1(?:_DIAG)?)?\.zip$/;
const SHA256 = /^[0-9a-f]{64}$/;
const enc = new TextEncoder();

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {status, headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store"}});
}
function serviceHeaders(extra:Record<string,string>={}) {return {apikey:SERVICE_ROLE_KEY,Authorization:`Bearer ${SERVICE_ROLE_KEY}`,...extra};}
async function rest(path:string, init:RequestInit={}) {return await fetch(`${SUPABASE_URL}/rest/v1/${path}`,{...init,headers:{...serviceHeaders({"content-type":"application/json"}),...(init.headers||{})}});}
async function sha256Bytes(bytes:Uint8Array) {const h=await crypto.subtle.digest("SHA-256",bytes);return [...new Uint8Array(h)].map(b=>b.toString(16).padStart(2,"0")).join("");}
async function sha256Text(value:string) {return await sha256Bytes(enc.encode(value));}
function unb64(value:string){const s=atob(value);const out=new Uint8Array(s.length);for(let i=0;i<s.length;i++)out[i]=s.charCodeAt(i);return out;}
async function vaultKey(){const raw=unb64(Deno.env.get("UKIE_TOKEN_VAULT_KEY_B64")??"");if(raw.byteLength!==32)throw new Error("VAULT_KEY_INVALID");return crypto.subtle.importKey("raw",raw,"AES-GCM",false,["decrypt"]);}
async function open(ciphertext:string,iv:string){const plain=await crypto.subtle.decrypt({name:"AES-GCM",iv:unb64(iv)},await vaultKey(),unb64(ciphertext));return new TextDecoder().decode(plain);}

async function workerIdentity(req:Request){
  const deviceKey=(req.headers.get("x-ukie-device-key")||"").trim(); const deviceToken=(req.headers.get("x-ukie-device-token")||"").trim();
  if(!DEVICE_KEY.test(deviceKey)||deviceToken.length<48||deviceToken.length>256)return null;
  const secretHash=await sha256Text(deviceToken);
  const q=new URLSearchParams({select:"id,user_id,device_key,status",device_key:`eq.${deviceKey}`,secret_hash:`eq.${secretHash}`,status:"eq.ACTIVE",limit:"1"});
  const res=await rest(`ukie_worker_devices?${q.toString()}`,{method:"GET"}); if(!res.ok)return null; const rows=await res.json();
  return Array.isArray(rows)&&rows.length===1?rows[0]:null;
}

async function googleAccessToken(userId:string):Promise<string>{
  const q=new URLSearchParams({select:"token_kind,ciphertext,iv,expires_at",user_id:`eq.${userId}`,provider:"eq.google",token_kind:"in.(access,refresh)"});
  const res=await rest(`ukie_provider_token_vault?${q.toString()}`,{method:"GET"}); if(!res.ok)throw new Error("VAULT_READ_FAILED");
  const rows=await res.json(); if(!Array.isArray(rows))throw new Error("VAULT_READ_FAILED");
  const access=rows.find((x:any)=>x.token_kind==="access");
  if(access?.ciphertext&&access?.iv&&access?.expires_at&&Date.parse(access.expires_at)>Date.now()+60_000)return await open(access.ciphertext,access.iv);
  const refresh=rows.find((x:any)=>x.token_kind==="refresh"); if(!refresh?.ciphertext||!refresh?.iv)throw new Error("GOOGLE_REFRESH_MISSING");
  const refreshToken=await open(refresh.ciphertext,refresh.iv);
  const clientId=Deno.env.get("GOOGLE_CLIENT_ID")??"",clientSecret=Deno.env.get("GOOGLE_CLIENT_SECRET")??"";
  if(!clientId||!clientSecret)throw new Error("GOOGLE_OAUTH_SERVER_SECRET_MISSING");
  const form=new URLSearchParams({client_id:clientId,client_secret:clientSecret,refresh_token:refreshToken,grant_type:"refresh_token"});
  const tokenRes=await fetch("https://oauth2.googleapis.com/token",{method:"POST",headers:{"content-type":"application/x-www-form-urlencoded"},body:form});
  const token=await tokenRes.json(); if(!tokenRes.ok||typeof token?.access_token!=="string")throw new Error("GOOGLE_REFRESH_FAILED");
  return token.access_token;
}

async function uploadAndReadback(token:string,name:string,bytes:Uint8Array){
  const boundary=`csmc_${crypto.randomUUID().replaceAll("-","")}`;
  const metadata=JSON.stringify({name,parents:[FIXED_DRIVE_FOLDER_ID]});
  const pre=enc.encode(`--${boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${metadata}\r\n--${boundary}\r\nContent-Type: application/zip\r\n\r\n`);
  const post=enc.encode(`\r\n--${boundary}--\r\n`);
  const body=new Blob([pre,bytes,post],{type:`multipart/related; boundary=${boundary}`});
  const up=await fetch("https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,size,parents",{method:"POST",headers:{Authorization:`Bearer ${token}`,"Content-Type":`multipart/related; boundary=${boundary}`},body});
  const info=await up.json(); if(!up.ok||typeof info?.id!=="string")throw new Error("DRIVE_UPLOAD_FAILED");
  const rb=await fetch(`https://www.googleapis.com/drive/v3/files/${encodeURIComponent(info.id)}?alt=media`,{headers:{Authorization:`Bearer ${token}`}});
  if(!rb.ok)throw new Error("DRIVE_READBACK_FAILED"); const readback=new Uint8Array(await rb.arrayBuffer());
  return {id:info.id,size:readback.byteLength,sha256:await sha256Bytes(readback)};
}

Deno.serve(async(req:Request)=>{
  try{
    if(req.method!=="POST")return json({ok:false,error:"method_not_allowed"},405);
    const worker=await workerIdentity(req); if(!worker)return json({ok:false,error:"device_auth"},403);
    const filename=(req.headers.get("x-csmc-filename")||"").trim(); const expectedSha=(req.headers.get("x-csmc-sha256")||"").trim().toLowerCase(); const expectedSize=Number(req.headers.get("x-csmc-size")||"-1");
    if(!CAPTURE_NAME.test(filename)||!SHA256.test(expectedSha)||!Number.isInteger(expectedSize)||expectedSize<=0||expectedSize>MAX_ARTIFACT_BYTES)return json({ok:false,error:"artifact_metadata_rejected"},400);
    const length=Number(req.headers.get("content-length")||"0"); if(length&&length!==expectedSize)return json({ok:false,error:"content_length_mismatch"},400); if(length>MAX_ARTIFACT_BYTES)return json({ok:false,error:"artifact_too_large"},413);
    const bytes=new Uint8Array(await req.arrayBuffer()); if(bytes.byteLength!==expectedSize||bytes.byteLength>MAX_ARTIFACT_BYTES)return json({ok:false,error:"artifact_size_mismatch"},400);
    const receivedSha=await sha256Bytes(bytes); if(receivedSha!==expectedSha)return json({ok:false,error:"artifact_sha_mismatch"},400);
    const token=await googleAccessToken(worker.user_id); const saved=await uploadAndReadback(token,filename,bytes);
    if(saved.size!==expectedSize||saved.sha256!==expectedSha)return json({ok:false,error:"drive_readback_mismatch",file_id:saved.id},502);
    return json({ok:true,status:"UPLOADED_READBACK_VERIFIED",file_id:saved.id,folder_id:FIXED_DRIVE_FOLDER_ID,filename,size:saved.size,sha256:saved.sha256,readback_verified:true,local_delete_requested:false,arbitrary_destination:false});
  }catch(e){const code=e instanceof Error?e.message.split(":",1)[0]:"UNKNOWN";return json({ok:false,error:code},500);}
});
