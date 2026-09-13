import { AI3D_PROJECT_KEY, sha256Hex, stableStringify } from './productionProtocol.js';
import { createModuleRegistry } from './moduleAssembly.js';

function isObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function assertString(value, name) {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${name} must be a non-empty string`);
  return value.trim();
}

function assertFinitePositive(value, name) {
  if (!Number.isFinite(value) || value <= 0) throw new Error(`${name} must be a positive finite number`);
  return value;
}

function normalizeRoom(room) {
  if (!isObject(room)) throw new Error('room must be an object');
  if (!Number.isInteger(room.id) || room.id < 0) throw new Error('room.id must be a non-negative integer');
  const name = assertString(room.name, 'room.name');
  const areaM2 = assertFinitePositive(room.areaM2, 'room.areaM2');
  if (!Array.isArray(room.center) || room.center.length !== 2 || room.center.some((v) => !Number.isFinite(v))) {
    throw new Error(`room ${room.id} center must be [x,y] finite coordinates`);
  }
  return {
    id: room.id,
    name,
    type: typeof room.type === 'string' && room.type.trim() ? room.type.trim() : 'Other',
    area_m2: areaM2,
    center_plan_xy_m: [room.center[0], room.center[1]],
  };
}

export function normalizeWalkMyPlanSnapshot(raw) {
  if (!isObject(raw)) throw new Error('walkmyplan snapshot must be an object');
  const planId = assertString(raw.plan_id, 'plan_id');
  const storeyHeightM = assertFinitePositive(raw.storey_height_m, 'storey_height_m');
  if (!Array.isArray(raw.rooms) || raw.rooms.length === 0) throw new Error('rooms must not be empty');
  const rooms = raw.rooms.map(normalizeRoom);
  const ids = new Set(rooms.map((room) => room.id));
  if (ids.size !== rooms.length) throw new Error('room ids must be unique');
  if (!isObject(raw.counts)) throw new Error('counts must be an object');
  const counts = {
    walls: Number(raw.counts.walls),
    openings: Number(raw.counts.openings),
    fixtures: Number(raw.counts.fixtures),
    rooms: Number(raw.counts.rooms ?? rooms.length),
  };
  for (const [key, value] of Object.entries(counts)) {
    if (!Number.isInteger(value) || value < 0) throw new Error(`counts.${key} must be a non-negative integer`);
  }
  if (counts.rooms !== rooms.length) throw new Error('counts.rooms does not match rooms length');
  return {
    plan_id: planId,
    source: 'WALKMYPLAN',
    storey_height_m: storeyHeightM,
    rooms,
    counts,
  };
}

export function createWalkMyPlanRoomModules(snapshot) {
  const normalized = normalizeWalkMyPlanSnapshot(snapshot);
  const prefix = normalized.plan_id.slice(0, 8).toUpperCase().replace(/[^A-Z0-9]/g, 'X');
  return normalized.rooms.map((room) => ({
    module_id: `WMP-${prefix}-ROOM-${room.id}`,
    kind: 'ROOM',
    artifact_id: `walkmyplan:${normalized.plan_id}:room:${room.id}`,
    source_artifact_ids: [`walkmyplan:${normalized.plan_id}`],
    dependencies: [],
    bounds: {},
    sockets: [],
    metadata: {
      source_provider: 'WALKMYPLAN',
      source_plan_id: normalized.plan_id,
      source_room_id: room.id,
      source_room_name: room.name,
      source_room_type: room.type,
      measured_area_m2: room.area_m2,
      source_center_plan_xy_m: room.center_plan_xy_m,
      source_storey_height_m: normalized.storey_height_m,
      geometry_detail: 'ROOM_SUMMARY_ONLY',
      dimensions_invented: false,
    },
  }));
}

function normalizeAdobeAsset(asset) {
  if (!isObject(asset)) throw new Error('adobe asset must be an object');
  return {
    asset_id: assertString(asset.id, 'adobe asset id'),
    name: assertString(asset.name, 'adobe asset name'),
    media_type: assertString(asset.mediaType, 'adobe asset mediaType'),
    canonical: false,
    use_scope: 'VISUAL_REFERENCE_ONLY',
    eligible_for_geometry_truth: false,
  };
}

function normalizeTo3DJob(job) {
  if (job == null) return null;
  if (!isObject(job)) throw new Error('to3d job must be an object');
  const status = assertString(job.status, 'to3d status').toLowerCase();
  return {
    job_id: assertString(job.job_id, 'to3d job_id'),
    status,
    output: job.output ?? null,
    eligible_for_import: status === 'completed' && Boolean(job.output),
    retry_policy: status === 'failed' ? 'NO_RETRY' : 'REVIEW',
    canonical: false,
  };
}

export async function createExternalFloorPlanIntakeArtifact({
  walkmyplan,
  adobe_assets = [],
  to3d_job = null,
  task_id = 'AI3D-006',
  run_id = 'AI3D-006-WALKMYPLAN-INTAKE',
}) {
  const source = normalizeWalkMyPlanSnapshot(walkmyplan);
  const modules = createWalkMyPlanRoomModules(walkmyplan);
  createModuleRegistry(modules);
  const references = {
    adobe: adobe_assets.map(normalizeAdobeAsset),
    to3d: normalizeTo3DJob(to3d_job),
  };
  const manifest = {
    schema: 'never-tear-ai3d-external-floor-plan-intake-v1',
    project_key: AI3D_PROJECT_KEY,
    task_id,
    run_id,
    source,
    modules,
    references,
    policy: {
      walkmyplan_role: 'MEASURED_FLOOR_PLAN_SOURCE',
      adobe_role: 'NON_CANONICAL_VISUAL_REFERENCE',
      to3d_failed_job_role: 'HISTORICAL_ONLY_NO_RETRY',
      do_not_invent_missing_dimensions: true,
      promotion_requires_downstream_qa: true,
    },
  };
  const sha256 = await sha256Hex(manifest);
  return {
    artifact_id: `floorplan-${sha256.slice(0, 16)}`,
    type: 'EXTERNAL_FLOOR_PLAN_INTAKE',
    project_key: AI3D_PROJECT_KEY,
    task_id,
    run_id,
    operation: 'EXTERNAL_FLOOR_PLAN_INTAKE',
    route: 'WALKMYPLAN_MODULE_REGISTRY',
    sha256,
    source_artifact_ids: [`walkmyplan:${source.plan_id}`],
    manifest,
    canonical_json: stableStringify(manifest),
    created_at: new Date().toISOString(),
  };
}

export async function qaExternalFloorPlanIntake({ artifact }) {
  const checks = [];
  const manifest = artifact?.manifest;
  let registryPass = false;
  try {
    createModuleRegistry(manifest?.modules);
    registryPass = true;
  } catch {
    registryPass = false;
  }
  checks.push({ name: 'artifact_schema', pass: artifact?.type === 'EXTERNAL_FLOOR_PLAN_INTAKE' && manifest?.schema === 'never-tear-ai3d-external-floor-plan-intake-v1' });
  checks.push({ name: 'project_lineage', pass: artifact?.project_key === AI3D_PROJECT_KEY && manifest?.project_key === AI3D_PROJECT_KEY });
  checks.push({ name: 'module_registry', pass: registryPass });
  checks.push({ name: 'room_count', pass: manifest?.source?.counts?.rooms === manifest?.modules?.length && manifest?.modules?.length === manifest?.source?.rooms?.length });
  checks.push({ name: 'measured_room_metadata', pass: manifest?.modules?.every((m) => Number.isFinite(m.metadata?.measured_area_m2) && Array.isArray(m.metadata?.source_center_plan_xy_m) && m.metadata.source_center_plan_xy_m.length === 2 && Number.isFinite(m.metadata?.source_storey_height_m)) === true });
  checks.push({ name: 'no_invented_dimensions', pass: manifest?.policy?.do_not_invent_missing_dimensions === true && manifest?.modules?.every((m) => Object.keys(m.bounds ?? {}).length === 0 && m.metadata?.dimensions_invented === false) === true });
  checks.push({ name: 'adobe_reference_boundary', pass: manifest?.references?.adobe?.every((a) => a.canonical === false && a.use_scope === 'VISUAL_REFERENCE_ONLY' && a.eligible_for_geometry_truth === false) === true });
  const to3d = manifest?.references?.to3d;
  checks.push({ name: 'to3d_failed_job_boundary', pass: !to3d || to3d.status !== 'failed' || (to3d.eligible_for_import === false && to3d.retry_policy === 'NO_RETRY' && to3d.canonical === false) });
  const expectedSha = await sha256Hex(manifest);
  checks.push({ name: 'artifact_sha_readback', pass: expectedSha === artifact?.sha256 });
  return {
    schema: 'never-tear-ai3d-external-floor-plan-intake-qa-v1',
    status: checks.every((check) => check.pass) ? 'PASS' : 'FAIL',
    checks,
    canonical_sha256: expectedSha,
    module_count: manifest?.modules?.length ?? 0,
  };
}
