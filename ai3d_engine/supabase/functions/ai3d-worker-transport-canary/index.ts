import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const admin = createClient(SUPABASE_URL, SERVICE_ROLE_KEY, {
  auth: { persistSession: false, autoRefreshToken: false },
});

const PROTOCOL = "never-tear-ai3d-worker-v1";
const BUCKET = "ai3d-evidence";
const ALLOWED_ACTIONS = new Set(["ai3d_blender_physical_mvp_v1"]);
const DEVICE_KEY_RE = /^[0-9a-zA-Z_-]{8,128}$/;
const HEX64 = /^[0-9a-f]{64}$/i;
const HEX_COLOR = /^#[0-9a-f]{6}$/i;
const MAX_JSON_BYTES = 128 * 1024;
const MAX_PNG_BYTES = 8 * 1024 * 1024;
const LEASE_SECONDS = 120;

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type, x-ukie-device-key, x-ukie-device-token, x-ai3d-job-id, x-ai3d-lease-owner, x-ai3d-png-sha256",
  "Access-Control-Allow-Methods": "POST, PUT, OPTIONS",
  "Cache-Control": "no-store",
};

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...cors, "Content-Type": "application/json; charset=utf-8" },
  });
}

async function sha256HexText(value: string) {
  const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function sha256HexBytes(value: ArrayBuffer) {
  const hash = await crypto.subtle.digest("SHA-256", value);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function workerIdentity(req: Request) {
  const deviceKey = (req.headers.get("x-ukie-device-key") || "").trim();
  const deviceToken = (req.headers.get("x-ukie-device-token") || "").trim();
  if (!DEVICE_KEY_RE.test(deviceKey) || deviceToken.length < 48 || deviceToken.length > 256) return null;
  const secretHash = await sha256HexText(deviceToken);
  const { data, error } = await admin
    .from("ukie_worker_devices")
    .select("id,user_id,device_key,status,worker_version,release_key,protocol_version,last_seen")
    .eq("device_key", deviceKey)
    .eq("secret_hash", secretHash)
    .eq("status", "ACTIVE")
    .maybeSingle();
  return error || !data ? null : data;
}

async function parseJsonBody(req: Request) {
  const length = Number(req.headers.get("content-length") || "0");
  if (length > MAX_JSON_BYTES) throw new Error("body_too_large");
  return await req.json();
}

function finiteNumber(value: unknown, min: number, max: number, fallback: number) {
  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  if (n < min || n > max) throw new Error("numeric_out_of_range");
  return n;
}

function vec3(value: unknown, fallback: [number, number, number], min: number, max: number): [number, number, number] {
  if (value === undefined || value === null) return fallback;
  if (!Array.isArray(value) || value.length !== 3) throw new Error("vec3_invalid");
  return [
    finiteNumber(value[0], min, max, fallback[0]),
    finiteNumber(value[1], min, max, fallback[1]),
    finiteNumber(value[2], min, max, fallback[2]),
  ];
}

function sanitizePlan(input: unknown) {
  const obj = input && typeof input === "object" && !Array.isArray(input) ? input as Record<string, unknown> : {};
  const object = obj.object && typeof obj.object === "object" && !Array.isArray(obj.object) ? obj.object as Record<string, unknown> : {};
  const material = object.material && typeof object.material === "object" && !Array.isArray(object.material) ? object.material as Record<string, unknown> : {};
  const camera = obj.camera && typeof obj.camera === "object" && !Array.isArray(obj.camera) ? obj.camera as Record<string, unknown> : {};
  const render = obj.render && typeof obj.render === "object" && !Array.isArray(obj.render) ? obj.render as Record<string, unknown> : {};

  const color = String(material.color_srgb ?? "#7c8792");
  if (!HEX_COLOR.test(color)) throw new Error("color_invalid");
  const engine = String(render.engine ?? "BLENDER_EEVEE_NEXT");
  if (engine !== "BLENDER_EEVEE_NEXT") throw new Error("engine_not_allowlisted");

  return {
    object: {
      name: "MVP_Physical_Box",
      kind: "box",
      size: vec3(object.size, [1.8, 1.2, 1.4], 0.05, 20),
      position: vec3(object.position, [1.0, 0.6, -2.0], -100, 100),
      rotation: vec3(object.rotation, [0.0, 0.35, 0.0], -6.283185307, 6.283185307),
      material: {
        color_srgb: color.toLowerCase(),
        roughness: finiteNumber(material.roughness, 0, 1, 0.42),
        metallic: finiteNumber(material.metallic, 0, 1, 0.12),
      },
    },
    camera: {
      position: vec3(camera.position, [6.5, 4.2, 7.5], -100, 100),
      target: vec3(camera.target, [1.0, 0.6, -2.0], -100, 100),
      lens_mm: finiteNumber(camera.lens_mm, 12, 200, 50),
    },
    render: {
      width: Math.round(finiteNumber(render.width, 64, 2048, 960)),
      height: Math.round(finiteNumber(render.height, 64, 2048, 540)),
      engine,
      output_format: "PNG",
      color_mode: "RGBA",
    },
  };
}

function cleanCapabilities(value: unknown) {
  if (!Array.isArray(value)) return [] as string[];
  return value.slice(0, 32).map((v) => String(v).slice(0, 120));
}

function cleanCompletion(value: unknown) {
  const obj = value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
  const rawPixelSha = String(obj.raw_pixel_sha256 || "").toLowerCase();
  const pngSha = String(obj.png_sha256 || "").toLowerCase();
  const checkpointSha = String(obj.checkpoint_sha256 || "").toLowerCase();
  const checkpointId = String(obj.checkpoint_id || "").slice(0, 120);
  const renderer = String(obj.renderer || "").slice(0, 160);
  const blenderVersion = String(obj.blender_version || "").slice(0, 80);
  const automatedQa = String(obj.automated_qa || "");
  const visualQa = String(obj.visual_qa || "PENDING");
  const width = Math.round(finiteNumber(obj.width, 64, 2048, 960));
  const height = Math.round(finiteNumber(obj.height, 64, 2048, 540));
  if (!HEX64.test(rawPixelSha) || !HEX64.test(pngSha) || !HEX64.test(checkpointSha)) throw new Error("completion_hash_invalid");
  if (!/^cp-[0-9a-zA-Z_-]{8,116}$/.test(checkpointId)) throw new Error("checkpoint_id_invalid");
  if (!renderer || !blenderVersion) throw new Error("renderer_metadata_missing");
  if (automatedQa !== "PASS") throw new Error("automated_qa_not_pass");
  if (visualQa !== "PENDING") throw new Error("visual_qa_must_be_pending");
  return { rawPixelSha, pngSha, checkpointSha, checkpointId, renderer, blenderVersion, automatedQa, visualQa, width, height };
}

async function fetchValidLease(jobId: string, leaseOwner: string, deviceKey: string) {
  const { data: job, error } = await admin
    .from("ai3d_worker_jobs")
    .select("*")
    .eq("id", jobId)
    .eq("device_key", deviceKey)
    .maybeSingle();
  if (error || !job) return { error: "job_not_found", job: null };
  if (!ALLOWED_ACTIONS.has(String(job.action))) return { error: "action_not_allowlisted", job: null };
  if (!["CLAIMED", "RUNNING"].includes(String(job.status))) return { error: "job_not_active", job: null };
  if (String(job.lease_owner || "") !== leaseOwner) return { error: "stale_lease", job: null };
  if (!job.lease_until || new Date(job.lease_until).getTime() < Date.now()) return { error: "lease_expired", job: null };
  return { error: null, job };
}

async function touchWorker(worker: any, ai3dWorkerVersion: string | null = null, capabilities: string[] | null = null) {
  const now = new Date().toISOString();
  const metadataPatch: Record<string, unknown> = {};
  if (ai3dWorkerVersion) {
    metadataPatch.ai3d_worker_version = ai3dWorkerVersion;
    metadataPatch.ai3d_contract_version = PROTOCOL;
  }
  if (capabilities) metadataPatch.ai3d_capabilities = capabilities;
  const { data: current } = await admin.from("ukie_worker_devices").select("metadata").eq("id", worker.id).maybeSingle();
  const metadata = { ...(current?.metadata || {}), ...metadataPatch, ai3d_last_seen: now };
  await admin.from("ukie_worker_devices").update({ last_seen: now, updated_at: now, last_error: null, metadata }).eq("id", worker.id);
  return now;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const worker = await workerIdentity(req);
  if (!worker) return json({ ok: false, error: "device_auth" }, 403);

  if (req.method === "PUT") {
    const contentType = (req.headers.get("content-type") || "").split(";")[0].trim().toLowerCase();
    const length = Number(req.headers.get("content-length") || "0");
    const jobId = (req.headers.get("x-ai3d-job-id") || "").trim();
    const leaseOwner = (req.headers.get("x-ai3d-lease-owner") || "").trim();
    const expectedPngSha = (req.headers.get("x-ai3d-png-sha256") || "").trim().toLowerCase();
    if (contentType !== "image/png") return json({ ok: false, error: "png_required" }, 415);
    if (!jobId || leaseOwner.length < 8 || !HEX64.test(expectedPngSha)) return json({ ok: false, error: "artifact_headers_invalid" }, 400);
    if (length <= 0 || length > MAX_PNG_BYTES) return json({ ok: false, error: "artifact_size_invalid" }, 413);

    const lease = await fetchValidLease(jobId, leaseOwner, worker.device_key);
    if (lease.error || !lease.job) return json({ ok: false, error: lease.error }, 409);

    const bytes = await req.arrayBuffer();
    if (bytes.byteLength <= 0 || bytes.byteLength > MAX_PNG_BYTES) return json({ ok: false, error: "artifact_size_invalid" }, 413);
    const prefix = new Uint8Array(bytes.slice(0, 8));
    const pngSignature = [137, 80, 78, 71, 13, 10, 26, 10];
    if (!pngSignature.every((v, i) => prefix[i] === v)) return json({ ok: false, error: "png_signature_invalid" }, 400);
    const uploadSha = await sha256HexBytes(bytes);
    if (uploadSha !== expectedPngSha) return json({ ok: false, error: "client_sha_mismatch" }, 409);

    const storagePath = `jobs/${jobId}/ai3d_physical_mvp.png`;
    const { error: uploadError } = await admin.storage.from(BUCKET).upload(storagePath, new Uint8Array(bytes), {
      contentType: "image/png",
      upsert: true,
      cacheControl: "0",
    });
    if (uploadError) return json({ ok: false, error: "storage_upload_failed" }, 500);

    const { data: readbackBlob, error: readbackError } = await admin.storage.from(BUCKET).download(storagePath);
    if (readbackError || !readbackBlob) return json({ ok: false, error: "storage_readback_failed" }, 500);
    const readbackBytes = await readbackBlob.arrayBuffer();
    const readbackSha = await sha256HexBytes(readbackBytes);
    if (readbackSha !== uploadSha) return json({ ok: false, error: "storage_readback_sha_mismatch" }, 500);

    const artifactId = `worker-render-${uploadSha.slice(0, 16)}`;
    const artifact = {
      artifact_id: artifactId,
      project_key: lease.job.project_key,
      task_id: lease.job.task_id,
      category: "PIXEL_RENDER_EVIDENCE",
      sha256: uploadSha,
      provider: "SUPABASE_STORAGE",
      uri: `supabase://${BUCKET}/${storagePath}`,
      qa_status: "AUTOMATED_PENDING",
      readback_status: "PASS",
      metadata: {
        worker_job_id: jobId,
        action: lease.job.action,
        physical_render: true,
        storage_bucket: BUCKET,
        storage_path: storagePath,
        png_sha256: uploadSha,
        size_bytes: bytes.byteLength,
        provider_readback_sha256: readbackSha,
        visual_qa: "PENDING",
      },
    };
    const { error: artifactError } = await admin.from("ai3d_artifacts").upsert(artifact, { onConflict: "artifact_id" });
    if (artifactError) return json({ ok: false, error: "artifact_ledger_write_failed" }, 500);

    const mergedResult = {
      ...(lease.job.result || {}),
      artifact: {
        artifact_id: artifactId,
        png_sha256: uploadSha,
        storage_bucket: BUCKET,
        storage_path: storagePath,
        size_bytes: bytes.byteLength,
        storage_readback_sha256: readbackSha,
        storage_readback_status: "PASS",
        visual_qa: "PENDING",
      },
    };
    const now = new Date().toISOString();
    await admin.from("ai3d_worker_jobs").update({ result: mergedResult, status: "RUNNING", lease_until: new Date(Date.now() + LEASE_SECONDS * 1000).toISOString(), updated_at: now }).eq("id", jobId).eq("lease_owner", leaseOwner);
    await admin.from("ai3d_worker_events").insert({ job_id: jobId, event_type: "ARTIFACT_READBACK_PASS", status: "RUNNING", device_key: worker.device_key, detail: { artifact_id: artifactId, png_sha256: uploadSha, size_bytes: bytes.byteLength } });
    await touchWorker(worker);
    return json({ ok: true, status: "ARTIFACT_READBACK_PASS", artifact_id: artifactId, png_sha256: uploadSha, readback_sha256: readbackSha, size_bytes: bytes.byteLength });
  }

  if (req.method !== "POST") return json({ ok: false, error: "method_not_allowed" }, 405);
  let body: any;
  try { body = await parseJsonBody(req); } catch (e) { return json({ ok: false, error: e instanceof Error ? e.message : "invalid_json" }, 400); }
  const action = String(body?.action || "");

  if (action === "heartbeat") {
    const ai3dWorkerVersion = String(body.ai3d_worker_version || "").slice(0, 80);
    const capabilities = cleanCapabilities(body.capabilities);
    if (!ai3dWorkerVersion || !capabilities.includes("ai3d_blender_physical_mvp_v1")) return json({ ok: false, error: "ai3d_capability_missing" }, 409);
    const now = await touchWorker(worker, ai3dWorkerVersion, capabilities);
    const jobId = String(body.job_id || "");
    const leaseOwner = String(body.lease_owner || "");
    if (jobId && leaseOwner) {
      const lease = await fetchValidLease(jobId, leaseOwner, worker.device_key);
      if (lease.error || !lease.job) return json({ ok: false, error: lease.error }, 409);
      const leaseUntil = new Date(Date.now() + LEASE_SECONDS * 1000).toISOString();
      await admin.from("ai3d_worker_jobs").update({ status: "RUNNING", lease_until: leaseUntil, updated_at: now }).eq("id", jobId).eq("lease_owner", leaseOwner);
      await admin.from("ai3d_worker_events").insert({ job_id: jobId, event_type: "HEARTBEAT", status: "RUNNING", device_key: worker.device_key, detail: { lease_until: leaseUntil, ai3d_worker_version: ai3dWorkerVersion, capabilities } });
      return json({ ok: true, status: "RUNNING", lease_until: leaseUntil, server_time: now, protocol_version: PROTOCOL });
    }
    return json({ ok: true, status: "ONLINE", server_time: now, protocol_version: PROTOCOL });
  }

  if (action === "claim") {
    const ai3dWorkerVersion = String(body.ai3d_worker_version || "").slice(0, 80);
    const capabilities = cleanCapabilities(body.capabilities);
    if (!ai3dWorkerVersion || !capabilities.includes("ai3d_blender_physical_mvp_v1")) return json({ ok: false, error: "ai3d_capability_missing" }, 409);
    const leaseOwner = `${worker.device_key}:${crypto.randomUUID()}`;
    const { data, error } = await admin.rpc("ai3d_claim_next_worker_job", {
      p_device_key: worker.device_key,
      p_lease_owner: leaseOwner,
      p_lease_seconds: LEASE_SECONDS,
    });
    if (error) return json({ ok: false, error: "claim_failed" }, 500);
    const job = Array.isArray(data) && data.length ? data[0] : null;
    if (!job) {
      await touchWorker(worker, ai3dWorkerVersion, capabilities);
      return json({ ok: true, status: "NO_JOB", job: null, protocol_version: PROTOCOL });
    }
    if (!ALLOWED_ACTIONS.has(String(job.action)) || !capabilities.includes(String(job.action))) {
      await admin.from("ai3d_worker_jobs").update({ status: "BLOCKED", error_code: "ACTION_NOT_ALLOWLISTED", lease_until: null, updated_at: new Date().toISOString() }).eq("id", job.id);
      return json({ ok: false, error: "action_not_allowlisted" }, 409);
    }
    let plan;
    try { plan = sanitizePlan(job.input); } catch (e) {
      await admin.from("ai3d_worker_jobs").update({ status: "BLOCKED", error_code: "INPUT_CONTRACT_INVALID", error_detail: { message: e instanceof Error ? e.message : "invalid_input" }, lease_until: null, updated_at: new Date().toISOString() }).eq("id", job.id);
      await admin.from("ai3d_worker_events").insert({ job_id: job.id, event_type: "INPUT_CONTRACT_REJECTED", status: "BLOCKED", device_key: worker.device_key, detail: { message: e instanceof Error ? e.message : "invalid_input" } });
      return json({ ok: false, error: "input_contract_invalid" }, 409);
    }
    await touchWorker(worker, ai3dWorkerVersion, capabilities);
    return json({
      ok: true,
      status: "CLAIMED",
      protocol_version: PROTOCOL,
      job: {
        id: job.id,
        job_key: job.job_key,
        command_id: job.command_id,
        project_key: job.project_key,
        task_id: job.task_id,
        action: job.action,
        contract_version: job.contract_version,
        lease_owner: job.lease_owner,
        lease_until: job.lease_until,
        attempt_count: job.attempt_count,
        max_attempts: job.max_attempts,
        plan,
      },
    });
  }

  if (action === "complete") {
    const jobId = String(body.job_id || "");
    const leaseOwner = String(body.lease_owner || "");
    const outcome = String(body.outcome || "");
    if (!jobId || leaseOwner.length < 8 || !["PASS", "FAIL"].includes(outcome)) return json({ ok: false, error: "completion_invalid" }, 400);
    const lease = await fetchValidLease(jobId, leaseOwner, worker.device_key);
    if (lease.error || !lease.job) return json({ ok: false, error: lease.error }, 409);
    const now = new Date().toISOString();

    if (outcome === "FAIL") {
      const errorCode = String(body.error_code || "AI3D_WORKER_ACTION_FAILED").slice(0, 120);
      const errorMessage = String(body.error_message || "").slice(0, 1000);
      await admin.from("ai3d_worker_jobs").update({ status: "FAIL", error_code: errorCode, error_detail: { message: errorMessage }, completed_at: now, lease_until: null, updated_at: now }).eq("id", jobId).eq("lease_owner", leaseOwner);
      await admin.from("ai3d_worker_events").insert({ job_id: jobId, event_type: "WORKER_FAILED", status: "FAIL", device_key: worker.device_key, detail: { error_code: errorCode } });
      const runKey = `AI3D-WORKER-${lease.job.job_key}`;
      await admin.from("ai3d_runs").upsert({ run_key: runKey, project_key: lease.job.project_key, task_id: lease.job.task_id, status: "FAIL", route: "WINDOWS_WORKER_BLENDER", command_plan: sanitizePlan(lease.job.input), qa_report: { automated_qa: "FAIL" }, error_summary: errorCode, started_at: lease.job.started_at || now, finished_at: now }, { onConflict: "run_key" });
      await touchWorker(worker);
      return json({ ok: true, status: "FAIL", job_key: lease.job.job_key, completed_at: now });
    }

    let completion;
    try { completion = cleanCompletion(body.result); } catch (e) { return json({ ok: false, error: e instanceof Error ? e.message : "completion_result_invalid" }, 409); }
    const savedArtifact = lease.job.result?.artifact || {};
    if (savedArtifact.storage_readback_status !== "PASS" || savedArtifact.png_sha256 !== completion.pngSha || !savedArtifact.artifact_id) {
      return json({ ok: false, error: "durable_artifact_readback_required" }, 409);
    }

    const plan = sanitizePlan(lease.job.input);
    const checkpointState = {
      project_key: lease.job.project_key,
      task_id: lease.job.task_id,
      route: "WINDOWS_WORKER_BLENDER",
      worker_job_id: jobId,
      command_id: lease.job.command_id,
      plan,
      render: {
        artifact_id: savedArtifact.artifact_id,
        png_sha256: completion.pngSha,
        raw_pixel_sha256: completion.rawPixelSha,
        renderer: completion.renderer,
        blender_version: completion.blenderVersion,
        width: completion.width,
        height: completion.height,
        storage_readback_status: "PASS",
      },
      automated_qa: "PASS",
      visual_qa: "PENDING",
      canary_promoted: false,
    };

    const { error: checkpointError } = await admin.from("ai3d_checkpoints").upsert({
      checkpoint_id: completion.checkpointId,
      project_key: lease.job.project_key,
      task_id: lease.job.task_id,
      run_key: `AI3D-WORKER-${lease.job.job_key}`,
      sha256: completion.checkpointSha,
      state_json: checkpointState,
      next_action: "Visually inspect the durable AI3D-002 Windows Worker PNG. If visual QA passes, complete AI3D-002 and unblock AI3D-004; do not promote from automated QA alone.",
    }, { onConflict: "checkpoint_id" });
    if (checkpointError) return json({ ok: false, error: "checkpoint_ledger_write_failed" }, 500);

    const { data: artifactRow } = await admin.from("ai3d_artifacts").select("metadata").eq("artifact_id", savedArtifact.artifact_id).maybeSingle();
    const artifactMetadata = {
      ...(artifactRow?.metadata || {}),
      raw_pixel_sha256: completion.rawPixelSha,
      png_sha256: completion.pngSha,
      renderer: completion.renderer,
      blender_version: completion.blenderVersion,
      width: completion.width,
      height: completion.height,
      automated_qa: "PASS",
      visual_qa: "PENDING",
      checkpoint_id: completion.checkpointId,
      checkpoint_sha256: completion.checkpointSha,
    };
    await admin.from("ai3d_artifacts").update({ qa_status: "AUTOMATED_PASS_VISUAL_PENDING", readback_status: "PASS", metadata: artifactMetadata }).eq("artifact_id", savedArtifact.artifact_id);

    const runKey = `AI3D-WORKER-${lease.job.job_key}`;
    const { error: runError } = await admin.from("ai3d_runs").upsert({
      run_key: runKey,
      project_key: lease.job.project_key,
      task_id: lease.job.task_id,
      status: "CANARY_AUTOMATED_PASS_VISUAL_PENDING",
      route: "WINDOWS_WORKER_BLENDER",
      command_plan: plan,
      qa_report: { automated_qa: "PASS", storage_readback: "PASS", visual_qa: "PENDING", artifact_id: savedArtifact.artifact_id },
      checkpoint_id: completion.checkpointId,
      error_summary: null,
      started_at: lease.job.started_at || now,
      finished_at: now,
    }, { onConflict: "run_key" });
    if (runError) return json({ ok: false, error: "run_ledger_write_failed" }, 500);

    const finalResult = {
      artifact: savedArtifact,
      raw_pixel_sha256: completion.rawPixelSha,
      png_sha256: completion.pngSha,
      checkpoint_id: completion.checkpointId,
      checkpoint_sha256: completion.checkpointSha,
      renderer: completion.renderer,
      blender_version: completion.blenderVersion,
      automated_qa: "PASS",
      visual_qa: "PENDING",
      canary_promoted: false,
    };
    const { error: jobError } = await admin.from("ai3d_worker_jobs").update({ status: "PASS", result: finalResult, completed_at: now, lease_until: null, updated_at: now, error_code: null, error_detail: {} }).eq("id", jobId).eq("lease_owner", leaseOwner);
    if (jobError) return json({ ok: false, error: "job_completion_write_failed" }, 500);

    const { data: task } = await admin.from("ai3d_tasks").select("artifact_refs,qa_summary").eq("task_id", lease.job.task_id).maybeSingle();
    if (task) {
      const refs = Array.isArray(task.artifact_refs) ? task.artifact_refs.map(String) : [];
      if (!refs.includes(savedArtifact.artifact_id)) refs.push(savedArtifact.artifact_id);
      const qaSummary = { ...(task.qa_summary || {}), windows_worker: { automated_qa: "PASS", storage_readback: "PASS", visual_qa: "PENDING", artifact_id: savedArtifact.artifact_id, checkpoint_id: completion.checkpointId } };
      await admin.from("ai3d_tasks").update({ status: "ACTIVE", stage: "QA", artifact_refs: refs, qa_summary: qaSummary, next_action: "Perform visual QA on the durable AI3D-002 Windows Worker Blender PNG. If PASS, complete AI3D-002 and unblock AI3D-004; do not promote from automated QA alone.", updated_at: now }).eq("task_id", lease.job.task_id);
    }
    await admin.from("ai3d_projects").update({ stage: "QA", next_action: "Perform visual QA on the durable AI3D-002 Windows Worker Blender PNG. If PASS, complete AI3D-002 and continue AI3D-004 through physicalQaGate.", updated_at: now }).eq("project_key", lease.job.project_key);
    await admin.from("ai3d_worker_events").insert({ job_id: jobId, event_type: "WORKER_CANARY_AUTOMATED_PASS", status: "PASS", device_key: worker.device_key, detail: { artifact_id: savedArtifact.artifact_id, checkpoint_id: completion.checkpointId, visual_qa: "PENDING" } });
    await touchWorker(worker);
    return json({ ok: true, status: "CANARY_AUTOMATED_PASS_VISUAL_PENDING", job_key: lease.job.job_key, artifact_id: savedArtifact.artifact_id, checkpoint_id: completion.checkpointId, completed_at: now, protocol_version: PROTOCOL });
  }

  return json({ ok: false, error: "unknown_action" }, 400);
});
