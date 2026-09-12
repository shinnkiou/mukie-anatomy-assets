const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const MAX_BODY_BYTES = 64 * 1024;
const DEVICE_KEY = /^[0-9a-zA-Z_-]{8,128}$/;
const ALLOWED_ACTION = "csmc_observer_capture";

function json(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

async function sha256Hex(value: string) {
  const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function parseBody(req: Request) {
  const length = Number(req.headers.get("content-length") || "0");
  if (length > MAX_BODY_BYTES) throw new Error("body_too_large");
  const raw = new Uint8Array(await req.arrayBuffer());
  if (raw.byteLength > MAX_BODY_BYTES) throw new Error("body_too_large");
  return JSON.parse(new TextDecoder().decode(raw));
}

function serviceHeaders(extra: Record<string, string> = {}) {
  return {
    apikey: SERVICE_ROLE_KEY,
    Authorization: `Bearer ${SERVICE_ROLE_KEY}`,
    "Content-Type": "application/json",
    ...extra,
  };
}

async function rest(path: string, init: RequestInit = {}) {
  return await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    headers: { ...serviceHeaders(), ...(init.headers || {}) },
  });
}

async function workerIdentity(req: Request) {
  const deviceKey = (req.headers.get("x-ukie-device-key") || "").trim();
  const deviceToken = (req.headers.get("x-ukie-device-token") || "").trim();
  if (!DEVICE_KEY.test(deviceKey) || deviceToken.length < 48 || deviceToken.length > 256) return null;
  const secretHash = await sha256Hex(deviceToken);
  const q = new URLSearchParams({
    select: "id,user_id,device_key,status,worker_version,release_key,protocol_version",
    device_key: `eq.${deviceKey}`,
    secret_hash: `eq.${secretHash}`,
    status: "eq.ACTIVE",
    limit: "1",
  });
  const res = await rest(`ukie_worker_devices?${q.toString()}`, { method: "GET" });
  if (!res.ok) return null;
  const rows = await res.json();
  return Array.isArray(rows) && rows.length === 1 ? rows[0] : null;
}

function sanitizeObserverResult(value: unknown) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  const v = value as Record<string, unknown>;
  const text = (key: string, max: number) => String(v[key] ?? "").slice(0, max);
  const integer = (key: string) => Math.max(0, Math.trunc(Number(v[key] ?? 0) || 0));
  const number = (key: string) => Math.max(0, Number(v[key] ?? 0) || 0);
  return {
    schema_version: text("schema_version", 120),
    action: text("action", 120),
    target: text("target", 160),
    existing_modeler_session_used: Boolean(v.existing_modeler_session_used),
    modeler_launch_performed: Boolean(v.modeler_launch_performed),
    model_load_performed: Boolean(v.model_load_performed),
    focus_change_performed: Boolean(v.focus_change_performed),
    scan_reason: text("scan_reason", 160),
    candidate_count: integer("candidate_count"),
    read_failures: integer("read_failures"),
    search_seconds: number("search_seconds"),
    payload_dumped: Boolean(v.payload_dumped),
    zip_name: text("zip_name", 260),
    zip_size: integer("zip_size"),
    zip_sha256: text("zip_sha256", 64),
    artifact_transfer: text("artifact_transfer", 120),
  };
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ ok: false, error: "method_not_allowed" }, 405);
  let body: any;
  try { body = await parseBody(req); }
  catch (e) { return json({ ok: false, error: e instanceof Error ? e.message : "invalid_json" }, 400); }

  const worker = await workerIdentity(req);
  if (!worker) return json({ ok: false, error: "device_auth" }, 403);
  const action = String(body?.action || "");

  if (action === "heartbeat") {
    return json({
      ok: true,
      status: "CSMC_CANARY_ONLINE",
      server_time: new Date().toISOString(),
      protocol_version: "ukie_worker_v1",
      canary: true,
      production_worker_state_mutated: false,
    });
  }

  if (action === "claim") {
    const leaseOwner = `${worker.device_key}:${crypto.randomUUID()}`;
    const res = await rest("rpc/ukie_claim_next_csmc_observer_job", {
      method: "POST",
      body: JSON.stringify({
        p_user_id: worker.user_id,
        p_device_key: worker.device_key,
        p_lease_owner: leaseOwner,
        p_lease_seconds: 300,
      }),
    });
    if (!res.ok) return json({ ok: false, error: "claim_failed" }, 500);
    const rows = await res.json();
    const job = Array.isArray(rows) && rows.length ? rows[0] : null;
    if (!job) return json({ ok: true, status: "NO_JOB", job: null, canary: true });
    if (String(job.action) !== ALLOWED_ACTION) return json({ ok: false, error: "action_not_allowlisted" }, 409);
    return json({
      ok: true,
      status: "CLAIMED",
      canary: true,
      job: {
        id: job.id,
        job_key: job.job_key,
        action: job.action,
        status: job.status,
        attempt_no: job.attempt_no,
        lease_owner: job.lease_owner,
        lease_until: job.lease_until,
        input_refs: {},
      },
      protocol_version: "ukie_worker_v1",
    });
  }

  if (action === "complete") {
    const jobId = String(body.job_id || "");
    const leaseOwner = String(body.lease_owner || "");
    const outcome = String(body.outcome || "");
    if (!jobId || leaseOwner.length < 8 || !["PASS", "FAIL"].includes(outcome)) {
      return json({ ok: false, error: "invalid_completion" }, 400);
    }
    const now = new Date().toISOString();
    const params = new URLSearchParams({
      id: `eq.${jobId}`,
      user_id: `eq.${worker.user_id}`,
      device_key: `eq.${worker.device_key}`,
      action: `eq.${ALLOWED_ACTION}`,
      status: "eq.CLAIMED",
      lease_owner: `eq.${leaseOwner}`,
      lease_until: `gt.${now}`,
      select: "id,job_key,status,attempt_no",
    });
    const finalStatus = outcome === "PASS" ? "COMPLETED" : "FAILED";
    const result = outcome === "PASS" ? sanitizeObserverResult(body.result) : {};
    const errorCode = outcome === "PASS" ? null : String(body.error_code || "CSMC_OBSERVER_FAILED").slice(0, 120);
    const errorDetail = outcome === "PASS" ? {} : {
      error_type: String(body?.error_detail?.error_type || "").slice(0, 160),
      error: String(body?.error_detail?.error || "").slice(0, 1000),
    };
    const res = await rest(`ukie_csmc_observer_jobs?${params.toString()}`, {
      method: "PATCH",
      headers: { Prefer: "return=representation" },
      body: JSON.stringify({
        status: finalStatus,
        result,
        error_code: errorCode,
        error_detail: errorDetail,
        completed_at: now,
        lease_until: null,
        updated_at: now,
      }),
    });
    if (!res.ok) return json({ ok: false, error: "completion_write_failed" }, 500);
    const rows = await res.json();
    if (!Array.isArray(rows) || rows.length !== 1) return json({ ok: false, error: "stale_or_expired_lease" }, 409);
    return json({ ok: true, status: finalStatus, job_key: rows[0].job_key, completed_at: now, canary: true });
  }

  return json({ ok: false, error: "unknown_action" }, 400);
});
