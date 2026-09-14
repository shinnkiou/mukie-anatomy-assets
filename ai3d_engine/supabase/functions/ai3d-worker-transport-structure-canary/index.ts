import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL");
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, { auth: { persistSession: false, autoRefreshToken: false } });

const PROTOCOL = "never-tear-ai3d-worker-v1";
const WORKER_VERSION = "0.2.0-ai3d-structure-canary";
const ACTION = "ai3d_structure_module_v1";
const TASK_ID = "AI3D-013";
const JOB_KEY = "AI3D-013-PHYSICAL-STRUCTURE-CANARY-001";
const COMMAND_ID = "AI3D-013-STRUCTURE-CANARY-001-NEVER-TEAR";
const RUN_ID = JOB_KEY;
const MODULE_ID = "ai3d_structure_capability_canary_v1";
const BUCKET = "ai3d-evidence";
const LEASE_SECONDS = 180;
const MAX_JSON_BYTES = 128 * 1024;
const MAX_PNG_BYTES = 8 * 1024 * 1024;
const DEVICE_KEY_RE = /^[0-9A-Za-z_-]{8,128}$/;
const HEX64 = /^[0-9a-f]{64}$/i;

const PLAN = {
  schema: "never-tear-ai3d-structure-capability-canary-plan-v1",
  project_key: "never_tear_ai3d_engine",
  task_id: TASK_ID,
  run_id: RUN_ID,
  module_id: MODULE_ID,
  coordinate_contract: "PLAN_XY_EAST_NORTH_TO_THREE_XZ_YUP_V1",
  commands: [
    { command_id: "ai3d-013-canary-create-wall", op: "CREATE_PRIMITIVE", params: { name: "wall_001", kind: "box", position: [0,1.7,0], size: [4,3.4,0.2] }, lineage: { module_id: MODULE_ID, source: "AI3D-013_SYNTHETIC_CANARY" }, routes: ["WINDOWS_WORKER"] },
    { command_id: "ai3d-013-canary-transform-wall", op: "TRANSFORM_SET", params: { name: "wall_001", rotation: [0,0,0] }, lineage: { module_id: MODULE_ID, source: "AI3D-013_SYNTHETIC_CANARY" }, routes: ["WINDOWS_WORKER"] },
    { command_id: "ai3d-013-canary-create-opening", op: "CREATE_PRIMITIVE", params: { name: "opening_cutter_001", kind: "box", position: [0,1.1,0], size: [1,2.2,0.6] }, lineage: { module_id: MODULE_ID, source: "AI3D-013_SYNTHETIC_CANARY" }, routes: ["WINDOWS_WORKER"] },
    { command_id: "ai3d-013-canary-transform-opening", op: "TRANSFORM_SET", params: { name: "opening_cutter_001", rotation: [0,0,0] }, lineage: { module_id: MODULE_ID, source: "AI3D-013_SYNTHETIC_CANARY" }, routes: ["WINDOWS_WORKER"] },
    { command_id: "ai3d-013-canary-boolean", op: "BOOLEAN", params: { target: "wall_001", tool: "opening_cutter_001", mode: "subtract", keep_tool: false }, lineage: { module_id: MODULE_ID, source: "AI3D-013_SYNTHETIC_CANARY" }, routes: ["WINDOWS_WORKER"] },
    { command_id: "ai3d-013-canary-qa", op: "QA_RUN", params: { checks: ["wall_count_exact","opening_boolean_exact","cutter_removed","mesh_nonempty","floor_contact","render_evidence"] }, lineage: { module_id: MODULE_ID, source: "AI3D-013_SYNTHETIC_CANARY" }, routes: ["WINDOWS_WORKER"] },
  ],
  policy: { synthetic_canary: true, geometry_authority_mutated: false, production_plan_mutated: false, allow_arbitrary_script: false, allow_network: false, max_commands: 6, max_attempts: 1, physical_concurrency: 1, semantic_promotion: false },
};

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type, x-ukie-device-key, x-ukie-device-token, x-ai3d-job-id, x-ai3d-lease-owner, x-ai3d-png-sha256",
  "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
  "Cache-Control": "no-store",
};

function reply(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { ...cors, "Content-Type": "application/json; charset=utf-8" } });
}
async function shaText(value) {
  const h = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(h)].map((b)=>b.toString(16).padStart(2,"0")).join("");
}
async function shaBytes(value) {
  const h = await crypto.subtle.digest("SHA-256", value);
  return [...new Uint8Array(h)].map((b)=>b.toString(16).padStart(2,"0")).join("");
}
async function identity(req) {
  const key = (req.headers.get("x-ukie-device-key") || "").trim();
  const token = (req.headers.get("x-ukie-device-token") || "").trim();
  if (!DEVICE_KEY_RE.test(key) || token.length < 48 || token.length > 256) return null;
  const secret = await shaText(token);
  const { data, error } = await admin.from("ukie_worker_devices")
    .select("id,device_key,status,metadata")
    .eq("device_key", key).eq("secret_hash", secret).eq("status", "ACTIVE").maybeSingle();
  return error || !data ? null : data;
}
function exactCompanion(body) {
  const caps = Array.isArray(body?.capabilities) ? body.capabilities.map(String) : [];
  return String(body?.ai3d_worker_version || "") === WORKER_VERSION && caps.length === 1 && caps[0] === ACTION;
}
async function touch(worker) {
  const now = new Date().toISOString();
  const metadata = { ...(worker.metadata || {}), ai3d_worker_version: WORKER_VERSION, ai3d_contract_version: PROTOCOL, ai3d_capabilities: [ACTION], ai3d_last_seen: now, ai3d_structure_canary_only: true };
  await admin.from("ukie_worker_devices").update({ last_seen: now, updated_at: now, last_error: null, metadata }).eq("id", worker.id);
  worker.metadata = metadata;
  return now;
}
async function armOnce() {
  const { data: old } = await admin.from("ai3d_worker_jobs").select("id,status,job_key,attempt_count,max_attempts").eq("job_key", JOB_KEY).maybeSingle();
  if (old) return old;
  const row = { job_key: JOB_KEY, command_id: COMMAND_ID, project_key: "never_tear_ai3d_engine", task_id: TASK_ID, action: ACTION, contract_version: PROTOCOL, status: "QUEUED", input: PLAN, result: {}, attempt_count: 0, max_attempts: 1, error_detail: {} };
  const { data, error } = await admin.from("ai3d_worker_jobs").insert(row).select("id,status,job_key,attempt_count,max_attempts").single();
  if (data && !error) {
    await admin.from("ai3d_worker_events").insert({ job_id: data.id, event_type: "STRUCTURE_CANARY_AUTO_ARMED", status: "QUEUED", detail: { worker_version: WORKER_VERSION, capability: ACTION } });
    return data;
  }
  const { data: raced } = await admin.from("ai3d_worker_jobs").select("id,status,job_key,attempt_count,max_attempts").eq("job_key", JOB_KEY).maybeSingle();
  if (raced) return raced;
  throw new Error(`canary_arm_failed:${error?.code || "unknown"}`);
}
async function lease(jobId, leaseOwner, deviceKey) {
  const { data: job, error } = await admin.from("ai3d_worker_jobs").select("*").eq("id", jobId).eq("device_key", deviceKey).maybeSingle();
  if (error || !job) return { error: "job_not_found" };
  if (job.job_key !== JOB_KEY || job.command_id !== COMMAND_ID || job.task_id !== TASK_ID || job.action !== ACTION || job.contract_version !== PROTOCOL) return { error: "job_identity_rejected" };
  if (job.status !== "RUNNING" || String(job.lease_owner || "") !== leaseOwner) return { error: "stale_lease" };
  if (!job.lease_until || new Date(job.lease_until).getTime() < Date.now()) return { error: "lease_expired" };
  return { job };
}
function cleanCompletion(body) {
  const r = body?.result || {};
  for (const k of ["raw_pixel_sha256","png_sha256","checkpoint_sha256"]) if (!HEX64.test(String(r[k] || ""))) throw new Error(`invalid_${k}`);
  if (String(r.automated_qa) !== "PASS" || String(r.visual_qa) !== "PENDING") throw new Error("qa_boundary_invalid");
  if (Number(r.wall_count) !== 1 || Number(r.opening_boolean_count) !== 1 || Number(r.command_count) !== 6) throw new Error("structure_counts_invalid");
  const checkpointId = String(r.checkpoint_id || "");
  if (checkpointId.length < 12 || checkpointId.length > 120) throw new Error("checkpoint_id_invalid");
  return {
    rawPixelSha: String(r.raw_pixel_sha256).toLowerCase(), pngSha: String(r.png_sha256).toLowerCase(), checkpointSha: String(r.checkpoint_sha256).toLowerCase(), checkpointId,
    renderer: String(r.renderer || "").slice(0,160), blenderVersion: String(r.blender_version || "").slice(0,80), renderEngine: String(r.render_engine || "").slice(0,80), booleanSolver: String(r.boolean_solver || "").slice(0,40),
    width: Number(r.width), height: Number(r.height),
  };
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const worker = await identity(req);
  if (!worker) return reply({ ok:false, error:"device_auth" }, 403);

  if (req.method === "PUT") {
    const jobId = (req.headers.get("x-ai3d-job-id") || "").trim();
    const owner = (req.headers.get("x-ai3d-lease-owner") || "").trim();
    const expected = (req.headers.get("x-ai3d-png-sha256") || "").trim().toLowerCase();
    const contentType = (req.headers.get("content-type") || "").split(";")[0].trim().toLowerCase();
    const length = Number(req.headers.get("content-length") || "0");
    if (!jobId || owner.length < 8 || !HEX64.test(expected) || contentType !== "image/png") return reply({ok:false,error:"artifact_headers_invalid"},400);
    if (length <= 0 || length > MAX_PNG_BYTES) return reply({ok:false,error:"artifact_size_invalid"},413);
    const active = await lease(jobId, owner, worker.device_key);
    if (!active.job) return reply({ok:false,error:active.error},409);
    const bytes = await req.arrayBuffer();
    if (bytes.byteLength <= 0 || bytes.byteLength > MAX_PNG_BYTES) return reply({ok:false,error:"artifact_size_invalid"},413);
    if ([...new Uint8Array(bytes.slice(0,8))].join(",") !== "137,80,78,71,13,10,26,10") return reply({ok:false,error:"png_signature_invalid"},400);
    const uploadSha = await shaBytes(bytes);
    if (uploadSha !== expected) return reply({ok:false,error:"client_sha_mismatch"},409);
    const storagePath = `structure_canary/jobs/${jobId}/ai3d_structure_capability_canary.png`;
    const { error: upErr } = await admin.storage.from(BUCKET).upload(storagePath, new Uint8Array(bytes), { contentType:"image/png", upsert:true, cacheControl:"0" });
    if (upErr) return reply({ok:false,error:"storage_upload_failed"},500);
    const { data: blob, error: dlErr } = await admin.storage.from(BUCKET).download(storagePath);
    if (dlErr || !blob) return reply({ok:false,error:"storage_readback_failed"},500);
    const readbackSha = await shaBytes(await blob.arrayBuffer());
    if (readbackSha !== uploadSha) return reply({ok:false,error:"storage_readback_sha_mismatch"},500);
    const artifactId = `structure-canary-render-${uploadSha.slice(0,16)}`;
    const artifact = { artifact_id: artifactId, project_key:"never_tear_ai3d_engine", task_id:TASK_ID, category:"PIXEL_RENDER_EVIDENCE", sha256:uploadSha, provider:"SUPABASE_STORAGE", uri:`supabase://${BUCKET}/${storagePath}`, qa_status:"AUTOMATED_PENDING", readback_status:"PASS", metadata:{ worker_job_id:jobId, action:ACTION, evidence_class:"PHYSICAL_WINDOWS_BLENDER_STRUCTURE_CAPABILITY_CANARY", storage_bucket:BUCKET, storage_path:storagePath, png_sha256:uploadSha, size_bytes:bytes.byteLength, provider_readback_sha256:readbackSha, visual_qa:"PENDING", canary_promoted:false } };
    const { error: artErr } = await admin.from("ai3d_artifacts").upsert(artifact,{onConflict:"artifact_id"});
    if (artErr) return reply({ok:false,error:"artifact_ledger_write_failed"},500);
    const now = new Date().toISOString();
    const merged = { ...(active.job.result || {}), artifact:{ artifact_id:artifactId, png_sha256:uploadSha, storage_bucket:BUCKET, storage_path:storagePath, size_bytes:bytes.byteLength, storage_readback_sha256:readbackSha, storage_readback_status:"PASS", visual_qa:"PENDING" } };
    await admin.from("ai3d_worker_jobs").update({ result:merged, status:"RUNNING", lease_until:new Date(Date.now()+LEASE_SECONDS*1000).toISOString(), updated_at:now }).eq("id",jobId).eq("lease_owner",owner);
    await admin.from("ai3d_worker_events").insert({ job_id:jobId,event_type:"STRUCTURE_CANARY_ARTIFACT_READBACK_PASS",status:"RUNNING",device_key:worker.device_key,detail:{artifact_id:artifactId,png_sha256:uploadSha,size_bytes:bytes.byteLength} });
    await touch(worker);
    return reply({ok:true,status:"ARTIFACT_READBACK_PASS",artifact_id:artifactId,png_sha256:uploadSha,readback_sha256:readbackSha,size_bytes:bytes.byteLength});
  }

  if (req.method !== "POST") return reply({ok:false,error:"method_not_allowed"},405);
  const length = Number(req.headers.get("content-length") || "0");
  if (length > MAX_JSON_BYTES) return reply({ok:false,error:"body_too_large"},413);
  let body;
  try { body = await req.json(); } catch { return reply({ok:false,error:"invalid_json"},400); }
  if (!exactCompanion(body)) return reply({ok:false,error:"structure_companion_identity_rejected"},409);

  if (body.action === "heartbeat") {
    const now = await touch(worker);
    const jobId = String(body.job_id || "");
    const owner = String(body.lease_owner || "");
    if (jobId && owner) {
      const active = await lease(jobId,owner,worker.device_key);
      if (!active.job) return reply({ok:false,error:active.error},409);
      const until = new Date(Date.now()+LEASE_SECONDS*1000).toISOString();
      await admin.from("ai3d_worker_jobs").update({lease_until:until,updated_at:now}).eq("id",jobId).eq("lease_owner",owner);
      await admin.from("ai3d_worker_events").insert({job_id:jobId,event_type:"STRUCTURE_CANARY_HEARTBEAT",status:"RUNNING",device_key:worker.device_key,detail:{lease_until:until,worker_version:WORKER_VERSION,capability:ACTION}});
      return reply({ok:true,status:"RUNNING",lease_until:until,protocol_version:PROTOCOL});
    }
    try {
      const canary = await armOnce();
      return reply({ok:true,status:"ONLINE",server_time:now,protocol_version:PROTOCOL,canary_job_key:JOB_KEY,canary_job_status:canary.status});
    } catch (e) { return reply({ok:false,error:e instanceof Error ? e.message : "canary_arm_failed"},500); }
  }

  if (body.action === "claim") {
    const owner = `${worker.device_key}:${crypto.randomUUID()}`;
    const { data, error } = await admin.rpc("ai3d_claim_structure_canary_job",{p_device_key:worker.device_key,p_lease_owner:owner,p_lease_seconds:LEASE_SECONDS});
    if (error) return reply({ok:false,error:"structure_claim_failed"},500);
    const job = Array.isArray(data) && data.length ? data[0] : null;
    if (!job) return reply({ok:true,status:"NO_JOB",job:null,protocol_version:PROTOCOL});
    return reply({ok:true,status:"CLAIMED",protocol_version:PROTOCOL,job:{id:job.id,job_key:job.job_key,command_id:job.command_id,project_key:job.project_key,task_id:job.task_id,action:job.action,contract_version:job.contract_version,lease_owner:job.lease_owner,lease_until:job.lease_until,attempt_count:job.attempt_count,max_attempts:job.max_attempts,plan:PLAN}});
  }

  if (body.action === "complete") {
    const jobId = String(body.job_id || "");
    const owner = String(body.lease_owner || "");
    const outcome = String(body.outcome || "");
    if (!jobId || owner.length < 8 || !["PASS","FAIL"].includes(outcome)) return reply({ok:false,error:"completion_invalid"},400);
    const active = await lease(jobId,owner,worker.device_key);
    if (!active.job) return reply({ok:false,error:active.error},409);
    const now = new Date().toISOString();
    if (outcome === "FAIL") {
      const code = String(body.error_code || "STRUCTURE_CANARY_FAILED").slice(0,120);
      const message = String(body.error_message || "").slice(0,1000);
      await admin.from("ai3d_worker_jobs").update({status:"FAIL",error_code:code,error_detail:{message},completed_at:now,lease_until:null,updated_at:now}).eq("id",jobId).eq("lease_owner",owner);
      await admin.from("ai3d_worker_events").insert({job_id:jobId,event_type:"STRUCTURE_CANARY_FAILED",status:"FAIL",device_key:worker.device_key,detail:{error_code:code}});
      await admin.from("ai3d_tasks").update({status:"ACTIVE",stage:"QA",next_action:"Preserve AI3D-013 failure evidence, fix the smallest cause, create a new bounded CANARY key/version, and do not unblock AI3D-010.",updated_at:now}).eq("task_id",TASK_ID);
      return reply({ok:true,status:"FAIL",job_key:JOB_KEY,completed_at:now});
    }
    let c;
    try { c = cleanCompletion(body); } catch (e) { return reply({ok:false,error:e instanceof Error ? e.message : "completion_result_invalid"},409); }
    const saved = active.job.result?.artifact || {};
    if (saved.storage_readback_status !== "PASS" || saved.png_sha256 !== c.pngSha || !saved.artifact_id) return reply({ok:false,error:"durable_artifact_readback_required"},409);
    const checkpointState = {task_id:TASK_ID,run_id:RUN_ID,module_id:MODULE_ID,action:ACTION,worker_job_id:jobId,artifact_id:saved.artifact_id,png_sha256:c.pngSha,raw_pixel_sha256:c.rawPixelSha,renderer:c.renderer,blender_version:c.blenderVersion,render_engine:c.renderEngine,boolean_solver:c.booleanSolver,wall_count:1,opening_boolean_count:1,command_count:6,automated_qa:"PASS",storage_readback:"PASS",visual_qa:"PENDING",canary_promoted:false};
    const { error: cpErr } = await admin.from("ai3d_checkpoints").upsert({checkpoint_id:c.checkpointId,project_key:"never_tear_ai3d_engine",task_id:TASK_ID,run_key:`AI3D-WORKER-${JOB_KEY}`,sha256:c.checkpointSha,state_json:checkpointState,next_action:"Perform visual QA on the durable AI3D-013 Structure CANARY PNG. Promote only if visual QA also passes."},{onConflict:"checkpoint_id"});
    if (cpErr) return reply({ok:false,error:"checkpoint_ledger_write_failed"},500);
    const runKey = `AI3D-WORKER-${JOB_KEY}`;
    const { error: runErr } = await admin.from("ai3d_runs").upsert({run_key:runKey,project_key:"never_tear_ai3d_engine",task_id:TASK_ID,status:"CANARY_AUTOMATED_PASS_VISUAL_PENDING",route:"WINDOWS_WORKER_BLENDER_STRUCTURE_CANARY",command_plan:PLAN,qa_report:{automated_qa:"PASS",storage_readback:"PASS",visual_qa:"PENDING",artifact_id:saved.artifact_id,wall_count:1,opening_boolean_count:1},checkpoint_id:c.checkpointId,error_summary:null,started_at:active.job.started_at||now,finished_at:now},{onConflict:"run_key"});
    if (runErr) return reply({ok:false,error:"run_ledger_write_failed"},500);
    const finalResult = {artifact:saved,raw_pixel_sha256:c.rawPixelSha,png_sha256:c.pngSha,checkpoint_id:c.checkpointId,checkpoint_sha256:c.checkpointSha,renderer:c.renderer,blender_version:c.blenderVersion,render_engine:c.renderEngine,boolean_solver:c.booleanSolver,automated_qa:"PASS",visual_qa:"PENDING",canary_promoted:false};
    const { error: jobErr } = await admin.from("ai3d_worker_jobs").update({status:"PASS",result:finalResult,completed_at:now,lease_until:null,updated_at:now,error_code:null,error_detail:{}}).eq("id",jobId).eq("lease_owner",owner);
    if (jobErr) return reply({ok:false,error:"job_completion_write_failed"},500);
    const { data: task } = await admin.from("ai3d_tasks").select("artifact_refs,qa_summary").eq("task_id",TASK_ID).maybeSingle();
    const refs = Array.isArray(task?.artifact_refs) ? task.artifact_refs.map(String) : [];
    if (!refs.includes(saved.artifact_id)) refs.push(saved.artifact_id);
    await admin.from("ai3d_tasks").update({status:"ACTIVE",stage:"QA",artifact_refs:refs,qa_summary:{...(task?.qa_summary||{}),structure_canary:{automated_qa:"PASS",storage_readback:"PASS",visual_qa:"PENDING",artifact_id:saved.artifact_id,checkpoint_id:c.checkpointId,structure_module_capability_promoted:false}},next_action:"Perform visual QA on AI3D-013 Structure CANARY. Only on PASS promote ai3d_structure_module_v1, complete RIO-60, and unblock AI3D-010.",updated_at:now}).eq("task_id",TASK_ID);
    await admin.from("ai3d_projects").update({next_action:"AI3D-013 Structure CANARY automated QA passed; visual QA is required before promotion or AI3D-010 production.",updated_at:now}).eq("project_key","never_tear_ai3d_engine");
    await admin.from("ai3d_worker_events").insert({job_id:jobId,event_type:"STRUCTURE_CANARY_AUTOMATED_PASS",status:"PASS",device_key:worker.device_key,detail:{artifact_id:saved.artifact_id,checkpoint_id:c.checkpointId,visual_qa:"PENDING",canary_promoted:false}});
    await touch(worker);
    return reply({ok:true,status:"STRUCTURE_CANARY_AUTOMATED_PASS_VISUAL_PENDING",job_key:JOB_KEY,artifact_id:saved.artifact_id,checkpoint_id:c.checkpointId,completed_at:now,protocol_version:PROTOCOL});
  }

  return reply({ok:false,error:"unknown_action"},400);
});
