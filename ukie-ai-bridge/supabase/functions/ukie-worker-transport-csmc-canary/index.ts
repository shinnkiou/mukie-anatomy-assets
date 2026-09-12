const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const MAX_BODY_BYTES = 64 * 1024;
const DEVICE_KEY = /^[0-9a-zA-Z_-]{8,128}$/;
const ALLOWED_JOB_ACTIONS = new Set(["csmc_observer_capture", "csmc_observer_diagnose_v1", "csmc_artifact_upload"]);

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {status, headers:{"Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store"}});
}
async function sha256Hex(value: string) {
  const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(hash)].map((b)=>b.toString(16).padStart(2,"0")).join("");
}
async function parseBody(req: Request) {
  const length=Number(req.headers.get("content-length")||"0"); if(length>MAX_BODY_BYTES) throw new Error("body_too_large");
  const raw=new Uint8Array(await req.arrayBuffer()); if(raw.byteLength>MAX_BODY_BYTES) throw new Error("body_too_large");
  return JSON.parse(new TextDecoder().decode(raw));
}
function serviceHeaders(extra:Record<string,string>={}) {return {apikey:SERVICE_ROLE_KEY,Authorization:`Bearer ${SERVICE_ROLE_KEY}`,"Content-Type":"application/json",...extra};}
async function rest(path:string, init:RequestInit={}) {return await fetch(`${SUPABASE_URL}/rest/v1/${path}`,{...init,headers:{...serviceHeaders(),...(init.headers||{})}});}
async function workerIdentity(req:Request) {
  const deviceKey=(req.headers.get("x-ukie-device-key")||"").trim(); const deviceToken=(req.headers.get("x-ukie-device-token")||"").trim();
  if(!DEVICE_KEY.test(deviceKey)||deviceToken.length<48||deviceToken.length>256) return null;
  const secretHash=await sha256Hex(deviceToken);
  const q=new URLSearchParams({select:"id,user_id,device_key,status,worker_version,release_key,protocol_version",device_key:`eq.${deviceKey}`,secret_hash:`eq.${secretHash}`,status:"eq.ACTIVE",limit:"1"});
  const res=await rest(`ukie_worker_devices?${q.toString()}`,{method:"GET"}); if(!res.ok) return null; const rows=await res.json();
  return Array.isArray(rows)&&rows.length===1?rows[0]:null;
}
const txt=(v:Record<string,unknown>,k:string,n:number)=>String(v[k]??"").slice(0,n);
const integer=(v:Record<string,unknown>,k:string)=>Math.max(0,Math.trunc(Number(v[k]??0)||0));
const number=(v:Record<string,unknown>,k:string)=>Math.max(0,Number(v[k]??0)||0);
function sanitizeResult(action:string,value:unknown) {
  if(!value||typeof value!=="object"||Array.isArray(value)) return {};
  const v=value as Record<string,unknown>;
  if(action==="csmc_artifact_upload") return {
    schema_version:txt(v,"schema_version",120), action, status:txt(v,"status",120), local_filename:txt(v,"local_filename",260),
    size:integer(v,"size"), sha256:txt(v,"sha256",64), drive_file_id:txt(v,"drive_file_id",256), drive_folder_id:txt(v,"drive_folder_id",256),
    readback_verified:Boolean(v.readback_verified), local_original_retained:Boolean(v.local_original_retained), arbitrary_url_enabled:false, arbitrary_path_enabled:false,
  };
  if(action==="csmc_observer_diagnose_v1") {
    const regions=(v.regions&&typeof v.regions==="object"&&!Array.isArray(v.regions)?v.regions:{}) as Record<string,unknown>;
    const pp=(v.predicate_pipeline&&typeof v.predicate_pipeline==="object"&&!Array.isArray(v.predicate_pipeline)?v.predicate_pipeline:{}) as Record<string,unknown>;
    const rf=(v.read_failures&&typeof v.read_failures==="object"&&!Array.isArray(v.read_failures)?v.read_failures:{}) as Record<string,unknown>;
    const details=Array.isArray(rf.details)?rf.details.slice(0,64).map((x:any)=>({region_base:String(x?.region_base??"").slice(0,32),region_size:Math.max(0,Math.trunc(Number(x?.region_size)||0)),offset:Math.max(0,Math.trunc(Number(x?.offset)||0)),type:String(x?.type??"").slice(0,64),type_raw:String(x?.type_raw??"").slice(0,32),protect:String(x?.protect??"").slice(0,32),requested_bytes:Math.max(0,Math.trunc(Number(x?.requested_bytes)||0)),win32_error:Math.max(0,Math.trunc(Number(x?.win32_error)||0))})):[];
    const rejects:Record<string,number>={}; if(v.reject_reason_counts&&typeof v.reject_reason_counts==="object"&&!Array.isArray(v.reject_reason_counts)){for(const [k,val] of Object.entries(v.reject_reason_counts as Record<string,unknown>).slice(0,64)) rejects[String(k).slice(0,120)]=Math.max(0,Math.trunc(Number(val)||0));}
    return {schema_version:txt(v,"schema_version",120),action,target:txt(v,"target",160),existing_modeler_session_used:Boolean(v.existing_modeler_session_used),modeler_launch_performed:false,model_load_performed:false,focus_change_performed:false,scan_reason:txt(v,"scan_reason",160),search_seconds:number(v,"search_seconds"),regions:{scanned_committed_readable:integer(regions,"scanned_committed_readable"),readable_mem_private:integer(regions,"readable_mem_private"),mapped:integer(regions,"mapped"),image:integer(regions,"image"),other:integer(regions,"other")},predicate_pipeline:{prefix_hits:integer(pp,"prefix_hits"),mem_private_prefix_hits:integer(pp,"mem_private_prefix_hits"),kind_character:integer(pp,"kind_character"),expected_guid:integer(pp,"expected_guid"),version_2:integer(pp,"version_2"),size_sanity:integer(pp,"size_sanity"),stored_align8_logical_eq_8:integer(pp,"stored_align8_logical_eq_8"),accepted:integer(pp,"accepted")},read_failures:{count:integer(rf,"count"),details_truncated:Boolean(rf.details_truncated),details},reject_reason_counts:rejects,payload_dumped:false,zip_name:txt(v,"zip_name",260),zip_size:integer(v,"zip_size"),zip_sha256:txt(v,"zip_sha256",64),artifact_transfer:txt(v,"artifact_transfer",120)};
  }
  return {schema_version:txt(v,"schema_version",120),action:txt(v,"action",120),target:txt(v,"target",160),existing_modeler_session_used:Boolean(v.existing_modeler_session_used),modeler_launch_performed:Boolean(v.modeler_launch_performed),model_load_performed:Boolean(v.model_load_performed),focus_change_performed:Boolean(v.focus_change_performed),scan_reason:txt(v,"scan_reason",160),candidate_count:integer(v,"candidate_count"),read_failures:integer(v,"read_failures"),search_seconds:number(v,"search_seconds"),payload_dumped:Boolean(v.payload_dumped),zip_name:txt(v,"zip_name",260),zip_size:integer(v,"zip_size"),zip_sha256:txt(v,"zip_sha256",64),artifact_transfer:txt(v,"artifact_transfer",120)};
}

Deno.serve(async(req)=>{
  if(req.method!=="POST") return json({ok:false,error:"method_not_allowed"},405);
  let body:any; try{body=await parseBody(req);}catch(e){return json({ok:false,error:e instanceof Error?e.message:"invalid_json"},400);}
  const worker=await workerIdentity(req); if(!worker) return json({ok:false,error:"device_auth"},403);
  const action=String(body?.action||"");
  if(action==="heartbeat") return json({ok:true,status:"CSMC_CANARY_ONLINE",server_time:new Date().toISOString(),protocol_version:"ukie_worker_v1",canary:true,production_worker_state_mutated:false});
  if(action==="claim") {
    const leaseOwner=`${worker.device_key}:${crypto.randomUUID()}`;
    const res=await rest("rpc/ukie_claim_next_csmc_observer_job",{method:"POST",body:JSON.stringify({p_user_id:worker.user_id,p_device_key:worker.device_key,p_lease_owner:leaseOwner,p_lease_seconds:300})});
    if(!res.ok) return json({ok:false,error:"claim_failed"},500); const rows=await res.json(); const job=Array.isArray(rows)&&rows.length?rows[0]:null;
    if(!job) return json({ok:true,status:"NO_JOB",job:null,canary:true});
    if(!ALLOWED_JOB_ACTIONS.has(String(job.action))) return json({ok:false,error:"action_not_allowlisted"},409);
    return json({ok:true,status:"CLAIMED",canary:true,job:{id:job.id,job_key:job.job_key,action:job.action,status:job.status,attempt_no:job.attempt_no,lease_owner:job.lease_owner,lease_until:job.lease_until,input_refs:{}},protocol_version:"ukie_worker_v1"});
  }
  if(action==="complete") {
    const jobId=String(body.job_id||""),leaseOwner=String(body.lease_owner||""),outcome=String(body.outcome||"");
    if(!jobId||leaseOwner.length<8||!["PASS","FAIL"].includes(outcome)) return json({ok:false,error:"invalid_completion"},400);
    const now=new Date().toISOString();
    const q=new URLSearchParams({id:`eq.${jobId}`,user_id:`eq.${worker.user_id}`,device_key:`eq.${worker.device_key}`,status:"eq.CLAIMED",lease_owner:`eq.${leaseOwner}`,lease_until:`gt.${now}`,select:"id,job_key,action,status,attempt_no"});
    const read=await rest(`ukie_csmc_observer_jobs?${q.toString()}`,{method:"GET"}); if(!read.ok) return json({ok:false,error:"completion_lookup_failed"},500); const current=await read.json();
    if(!Array.isArray(current)||current.length!==1||!ALLOWED_JOB_ACTIONS.has(String(current[0].action))) return json({ok:false,error:"stale_or_invalid_job"},409);
    const jobAction=String(current[0].action); const finalStatus=outcome==="PASS"?"COMPLETED":"FAILED";
    const result=outcome==="PASS"?sanitizeResult(jobAction,body.result):{}; const errorCode=outcome==="PASS"?null:String(body.error_code||"CSMC_ACTION_FAILED").slice(0,120);
    const errorDetail=outcome==="PASS"?{}:{error_type:String(body?.error_detail?.error_type||"").slice(0,160),error:String(body?.error_detail?.error||"").slice(0,1000)};
    const res=await rest(`ukie_csmc_observer_jobs?${q.toString()}`,{method:"PATCH",headers:{Prefer:"return=representation"},body:JSON.stringify({status:finalStatus,result,error_code:errorCode,error_detail:errorDetail,completed_at:now,lease_until:null,updated_at:now})});
    if(!res.ok) return json({ok:false,error:"completion_write_failed"},500); const rows=await res.json(); if(!Array.isArray(rows)||rows.length!==1) return json({ok:false,error:"stale_or_expired_lease"},409);
    return json({ok:true,status:finalStatus,job_key:rows[0].job_key,completed_at:now,canary:true});
  }
  return json({ok:false,error:"unknown_action"},400);
});
