import fs from 'node:fs/promises';
import path from 'node:path';
import {
  createVisualQaReview,
  evaluatePhysicalPromotionGate,
  REQUIRED_ACTION,
} from '../src/physicalQaGate.js';

const OUT = path.resolve('artifacts/ai3d_physical_qa_gate');
await fs.mkdir(OUT, { recursive: true });

const workerResult = {
  schema_version: 'never-tear-ai3d-worker-render-v1',
  action: REQUIRED_ACTION,
  status: 'PASS',
  coordinate_contract: 'THREE_Y_UP_TO_BLENDER_Z_UP_V1',
  png_sha256: 'a'.repeat(64),
  raw_pixel_sha256: 'b'.repeat(64),
  raw_pixel_format: 'RGBA_FLOAT32_DECODED_PNG',
  renderer: 'Blender 4.2.23 LTS / EEVEE Next',
  width: 960,
  height: 540,
  automated_qa: 'PASS',
  visual_qa: 'PENDING',
  canary_promoted: false,
};

const capabilityEvidence = {
  device_key: 'ai3d-test-device-key',
  worker_version: '0.1.0-ai3d-canary',
  protocol_version: 'never-tear-ai3d-worker-v1',
  contract_version: 'never-tear-ai3d-worker-v1',
  capabilities: [REQUIRED_ACTION],
  observed_at: new Date().toISOString(),
};

const providerReadback = {
  provider: 'SUPABASE_STORAGE',
  uri: 'private://ai3d-evidence/test/ai3d_physical_mvp.png',
  readback_status: 'PASS',
  png_sha256: workerResult.png_sha256,
};

const visualReview = await createVisualQaReview(workerResult, {
  reviewer_mode: 'SYNTHETIC_GATE_SMOKE_ONLY',
  geometry_valid: true,
  floor_contact_valid: true,
  material_visible: true,
  framing_sensible: true,
  image_not_corrupt: true,
  notes: 'Logic-only gate smoke. This is not physical execution evidence and must never be promoted as such.',
});

const positive = await evaluatePhysicalPromotionGate({
  workerResult,
  capabilityEvidence,
  providerReadback,
  visualReview,
  route: 'WINDOWS_COMPANION_BLENDER_EEVEE_NEXT',
});

const pendingVisual = await evaluatePhysicalPromotionGate({
  workerResult,
  capabilityEvidence,
  providerReadback,
  visualReview: { ...visualReview, status: 'PENDING' },
  route: 'WINDOWS_COMPANION_BLENDER_EEVEE_NEXT',
});

const hashMismatch = await evaluatePhysicalPromotionGate({
  workerResult,
  capabilityEvidence,
  providerReadback: { ...providerReadback, png_sha256: 'c'.repeat(64) },
  visualReview,
  route: 'WINDOWS_COMPANION_BLENDER_EEVEE_NEXT',
});

const legacyWorker = await evaluatePhysicalPromotionGate({
  workerResult,
  capabilityEvidence: {
    ...capabilityEvidence,
    worker_version: '0.18.2-p0.18.2',
    contract_version: 'ukie_worker_v1',
    capabilities: [],
  },
  providerReadback,
  visualReview,
  route: 'WINDOWS_COMPANION_BLENDER_EEVEE_NEXT',
});

const virtualRoute = await evaluatePhysicalPromotionGate({
  workerResult,
  capabilityEvidence,
  providerReadback,
  visualReview,
  route: 'VIRTUAL_WORKER',
});

const assertions = {
  valid_complete_evidence_promotes: positive.decision === 'PROMOTE' && positive.canary_promoted === true,
  pending_visual_holds: pendingVisual.decision === 'HOLD' && pendingVisual.canary_promoted === false,
  provider_hash_mismatch_holds: hashMismatch.decision === 'HOLD',
  legacy_worker_holds: legacyWorker.decision === 'HOLD',
  virtual_route_holds: virtualRoute.decision === 'HOLD',
};

if (!Object.values(assertions).every(Boolean)) {
  console.error(JSON.stringify({ assertions, positive, pendingVisual, hashMismatch, legacyWorker, virtualRoute }, null, 2));
  process.exit(1);
}

const result = {
  schema: 'never-tear-ai3d-physical-qa-gate-smoke-v1',
  task_id: 'AI3D-004',
  status: 'PASS',
  evidence_class: 'LOGIC_ONLY_NOT_PHYSICAL',
  physical_execution_claimed: false,
  assertions,
  positive_decision: positive.decision,
  negative_decisions: {
    pending_visual: pendingVisual.decision,
    provider_hash_mismatch: hashMismatch.decision,
    legacy_worker: legacyWorker.decision,
    virtual_route: virtualRoute.decision,
  },
  gate_sha256: positive.sha256,
  visual_review_sha256: visualReview.sha256,
  next_action: 'Wait for verified AI3D Windows companion capability, run exactly one physical CANARY, then feed real result/provider readback/visual review through this gate.',
};

await fs.writeFile(path.join(OUT, 'physical_qa_gate_smoke_result.json'), `${JSON.stringify(result, null, 2)}\n`, 'utf8');
console.log(JSON.stringify(result, null, 2));
