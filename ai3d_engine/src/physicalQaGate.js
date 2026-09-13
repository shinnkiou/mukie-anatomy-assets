import { sha256Hex, stableStringify } from './productionProtocol.js';

export const PHYSICAL_QA_GATE_SCHEMA = 'never-tear-ai3d-physical-qa-gate-v1';
export const REQUIRED_WORKER_SCHEMA = 'never-tear-ai3d-worker-render-v1';
export const REQUIRED_ACTION = 'ai3d_blender_physical_mvp_v1';
export const REQUIRED_CONTRACT = 'never-tear-ai3d-worker-v1';
export const REQUIRED_COORDINATE_CONTRACT = 'THREE_Y_UP_TO_BLENDER_Z_UP_V1';
export const LEGACY_INELIGIBLE_WORKER = '0.18.2-p0.18.2';

const SHA256_RE = /^[0-9a-f]{64}$/i;

function isObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function pass(name, ok, detail = null) {
  return { name, status: ok ? 'PASS' : 'FAIL', detail };
}

function normalizedCapabilityEvidence(value = {}) {
  return {
    worker_version: value.worker_version ?? null,
    protocol_version: value.protocol_version ?? null,
    contract_version: value.contract_version ?? null,
    capabilities: Array.isArray(value.capabilities) ? [...value.capabilities] : [],
    device_key: value.device_key ?? null,
    observed_at: value.observed_at ?? null,
  };
}

export function inspectWorkerResult(workerResult) {
  const r = isObject(workerResult) ? workerResult : {};
  const checks = [
    pass('worker_schema', r.schema_version === REQUIRED_WORKER_SCHEMA, r.schema_version ?? null),
    pass('allowlisted_action', r.action === REQUIRED_ACTION, r.action ?? null),
    pass('physical_status', r.status === 'PASS', r.status ?? null),
    pass('automated_qa', r.automated_qa === 'PASS', r.automated_qa ?? null),
    pass('coordinate_contract', r.coordinate_contract === REQUIRED_COORDINATE_CONTRACT, r.coordinate_contract ?? null),
    pass('png_sha256', SHA256_RE.test(String(r.png_sha256 ?? ''))),
    pass('raw_pixel_sha256', SHA256_RE.test(String(r.raw_pixel_sha256 ?? ''))),
    pass('pixel_hash_distinct', Boolean(r.png_sha256 && r.raw_pixel_sha256 && r.png_sha256 !== r.raw_pixel_sha256)),
    pass('dimensions', Number.isInteger(r.width) && r.width >= 64 && r.width <= 4096 && Number.isInteger(r.height) && r.height >= 64 && r.height <= 4096, `${r.width ?? '?'}x${r.height ?? '?'}`),
    pass('visual_state_bounded', ['PENDING', 'PASS', 'FAIL'].includes(r.visual_qa), r.visual_qa ?? null),
  ];
  return {
    status: checks.every((c) => c.status === 'PASS') ? 'PASS' : 'FAIL',
    checks,
  };
}

export function inspectCapabilityEvidence(capabilityEvidence) {
  const c = normalizedCapabilityEvidence(capabilityEvidence);
  const checks = [
    pass('device_key_present', typeof c.device_key === 'string' && c.device_key.length >= 8),
    pass('separate_ai3d_contract', c.contract_version === REQUIRED_CONTRACT, c.contract_version),
    pass('ai3d_capability_advertised', c.capabilities.includes(REQUIRED_ACTION), c.capabilities),
    pass('legacy_worker_rejected', c.worker_version !== LEGACY_INELIGIBLE_WORKER, c.worker_version),
  ];
  return {
    status: checks.every((x) => x.status === 'PASS') ? 'PASS' : 'FAIL',
    evidence: c,
    checks,
  };
}

export function inspectProviderReadback(workerResult, providerReadback) {
  const p = isObject(providerReadback) ? providerReadback : {};
  const checks = [
    pass('provider_is_durable', typeof p.provider === 'string' && !['VIRTUAL', 'MEMORY', 'SYNTHETIC'].includes(p.provider.toUpperCase()), p.provider ?? null),
    pass('readback_status', p.readback_status === 'PASS', p.readback_status ?? null),
    pass('provider_png_sha_matches', p.png_sha256 === workerResult?.png_sha256, p.png_sha256 ?? null),
    pass('provider_uri_present', typeof p.uri === 'string' && p.uri.length > 0),
  ];
  return {
    status: checks.every((c) => c.status === 'PASS') ? 'PASS' : 'FAIL',
    checks,
  };
}

export async function createVisualQaReview(workerResult, review) {
  if (!isObject(review)) throw new Error('review must be an object');
  const criteria = {
    geometry_valid: review.geometry_valid === true,
    floor_contact_valid: review.floor_contact_valid === true,
    material_visible: review.material_visible === true,
    framing_sensible: review.framing_sensible === true,
    image_not_corrupt: review.image_not_corrupt === true,
  };
  const status = Object.values(criteria).every(Boolean) ? 'PASS' : 'FAIL';
  const record = {
    schema: 'never-tear-ai3d-visual-qa-v1',
    artifact_png_sha256: workerResult?.png_sha256 ?? null,
    raw_pixel_sha256: workerResult?.raw_pixel_sha256 ?? null,
    reviewer_mode: review.reviewer_mode ?? 'VISION_REVIEW',
    criteria,
    notes: review.notes ?? null,
    status,
  };
  return {
    ...record,
    sha256: await sha256Hex(stableStringify(record)),
  };
}

export async function evaluatePhysicalPromotionGate({
  workerResult,
  capabilityEvidence,
  providerReadback,
  visualReview,
  route,
}) {
  const worker = inspectWorkerResult(workerResult);
  const capability = inspectCapabilityEvidence(capabilityEvidence);
  const provider = inspectProviderReadback(workerResult, providerReadback);
  const visual = isObject(visualReview) ? visualReview : { status: 'MISSING' };
  const routeCheck = pass(
    'physical_route_only',
    typeof route === 'string' && route.length > 0 && !/VIRTUAL|HEADLESS_WEBGL_SYNTHETIC|MOCK/i.test(route),
    route ?? null,
  );
  const visualCheck = pass('visual_qa_pass', visual.status === 'PASS', visual.status ?? null);
  const workerVisualStateCheck = pass('worker_visual_not_pre_promoted', workerResult?.visual_qa !== 'PASS' || workerResult?.canary_promoted !== true, {
    visual_qa: workerResult?.visual_qa ?? null,
    canary_promoted: workerResult?.canary_promoted ?? null,
  });

  const checks = [
    ...worker.checks,
    ...capability.checks,
    ...provider.checks,
    routeCheck,
    visualCheck,
    workerVisualStateCheck,
  ];
  const allPass = checks.every((c) => c.status === 'PASS');
  const record = {
    schema: PHYSICAL_QA_GATE_SCHEMA,
    action: REQUIRED_ACTION,
    decision: allPass ? 'PROMOTE' : 'HOLD',
    canary_promoted: allPass,
    worker_png_sha256: workerResult?.png_sha256 ?? null,
    visual_qa_sha256: visual.sha256 ?? null,
    capability: capability.evidence,
    provider: {
      provider: providerReadback?.provider ?? null,
      uri: providerReadback?.uri ?? null,
      readback_status: providerReadback?.readback_status ?? null,
    },
    route: route ?? null,
    checks,
    next_action: allPass
      ? 'Record promoted physical artifact/checkpoint and continue AI3D-004 completion sync.'
      : 'Do not promote. Satisfy every failed physical/capability/provider/visual gate and re-evaluate.',
  };
  return {
    ...record,
    sha256: await sha256Hex(stableStringify(record)),
  };
}
