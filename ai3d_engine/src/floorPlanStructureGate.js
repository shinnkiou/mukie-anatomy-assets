import { AI3D_PROJECT_KEY, sha256Hex, stableStringify } from './productionProtocol.js';

function isObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function finite(value) {
  return Number.isFinite(value);
}

function positiveInt(value) {
  return Number.isInteger(value) && value >= 0;
}

function normalizeCounts(input = {}) {
  const counts = input.counts ?? {};
  const walls = Number(counts.walls ?? 0);
  const openings = Number(counts.openings ?? 0);
  const fixtures = Number(counts.fixtures ?? 0);
  const rooms = Number(counts.rooms ?? 0);
  for (const [key, value] of Object.entries({ walls, openings, fixtures, rooms })) {
    if (!positiveInt(value)) throw new Error(`counts.${key} must be a non-negative integer`);
  }
  return { walls, openings, fixtures, rooms };
}

function validWall(wall) {
  return isObject(wall)
    && (Number.isInteger(wall.wall_id) || Number.isInteger(wall.id))
    && finite(wall.x1) && finite(wall.y1) && finite(wall.x2) && finite(wall.y2)
    && !(wall.x1 === wall.x2 && wall.y1 === wall.y2);
}

function validOpening(opening) {
  if (!isObject(opening)) return false;
  const hasId = Number.isInteger(opening.opening_id) || Number.isInteger(opening.id);
  const hasWall = Number.isInteger(opening.wall_id);
  const kindOk = opening.kind === 'door' || opening.kind === 'window';
  const hasSpan = finite(opening.span_from_m) && finite(opening.span_to_m) && opening.span_to_m > opening.span_from_m;
  const hasCenter = Array.isArray(opening.center_xy_m)
    && opening.center_xy_m.length === 2
    && opening.center_xy_m.every(finite);
  return hasId && hasWall && kindOk && (hasSpan || hasCenter);
}

export function evaluateFloorPlanStructureSource(source) {
  if (!isObject(source)) throw new Error('source must be an object');
  const counts = normalizeCounts(source);
  const provider = typeof source.source === 'string'
    ? source.source
    : typeof source.provider === 'string'
      ? source.provider
      : 'UNKNOWN';
  const sourceRole = typeof source.source_role === 'string'
    ? source.source_role
    : provider === 'WALKMYPLAN'
      ? 'MEASURED_FLOOR_PLAN_SOURCE'
      : 'UNKNOWN';

  const walls = Array.isArray(source.walls) ? source.walls : [];
  const openings = Array.isArray(source.openings) ? source.openings : [];
  const allowedProvider = ['WALKMYPLAN', 'CAD_IMPORT', 'AUTHORITATIVE_GEOMETRY'].includes(provider);
  const wallGeometryComplete = counts.walls === walls.length && walls.every(validWall);
  const openingGeometryComplete = counts.openings === openings.length && openings.every(validOpening);
  const roleEligible = sourceRole === 'MEASURED_FLOOR_PLAN_SOURCE' || sourceRole === 'AUTHORITATIVE_GEOMETRY_SOURCE';

  const reasons = [];
  if (!allowedProvider) reasons.push('NON_AUTHORITATIVE_PROVIDER');
  if (!roleEligible) reasons.push('NON_AUTHORITATIVE_SOURCE_ROLE');
  if (counts.walls > 0 && walls.length === 0) reasons.push('WALL_GEOMETRY_MISSING');
  else if (!wallGeometryComplete) reasons.push('WALL_GEOMETRY_INCOMPLETE');
  if (counts.openings > 0 && openings.length === 0) reasons.push('OPENING_GEOMETRY_MISSING');
  else if (!openingGeometryComplete) reasons.push('OPENING_GEOMETRY_INCOMPLETE');

  const ready = allowedProvider && roleEligible && wallGeometryComplete && openingGeometryComplete;
  return {
    schema: 'never-tear-ai3d-floor-plan-structure-gate-v1',
    project_key: AI3D_PROJECT_KEY,
    status: ready ? 'READY' : 'HOLD',
    promotion: ready ? 'ALLOW_STRUCTURE_COMPILE' : 'BLOCK_STRUCTURE_COMPILE',
    provider,
    source_role: sourceRole,
    counts,
    observed: {
      walls_with_geometry: walls.length,
      openings_with_geometry: openings.length,
    },
    checks: {
      authoritative_provider: allowedProvider,
      authoritative_source_role: roleEligible,
      wall_geometry_complete: wallGeometryComplete,
      opening_geometry_complete: openingGeometryComplete,
      no_dimension_inference_required: ready,
    },
    reasons,
    policy: {
      infer_missing_wall_endpoints: false,
      infer_room_dimensions_from_area: false,
      infer_opening_positions: false,
      adobe_visual_reference_can_supply_geometry: false,
      failed_to3d_job_can_supply_geometry: false,
    },
  };
}

export async function createFloorPlanStructureGateArtifact({ source, task_id = 'AI3D-007', run_id = 'AI3D-007-STRUCTURE-SOURCE-GATE' }) {
  const gate = evaluateFloorPlanStructureSource(source);
  const manifest = {
    schema: 'never-tear-ai3d-floor-plan-structure-gate-artifact-v1',
    project_key: AI3D_PROJECT_KEY,
    task_id,
    run_id,
    gate,
  };
  const sha256 = await sha256Hex(manifest);
  return {
    artifact_id: `structure-gate-${sha256.slice(0, 16)}`,
    type: 'FLOOR_PLAN_STRUCTURE_SOURCE_GATE',
    project_key: AI3D_PROJECT_KEY,
    task_id,
    run_id,
    operation: 'STRUCTURE_SOURCE_GATE',
    route: 'SOURCE_VALIDATION_ONLY',
    sha256,
    manifest,
    canonical_json: stableStringify(manifest),
    created_at: new Date().toISOString(),
  };
}

export async function qaFloorPlanStructureGateArtifact({ artifact }) {
  const expected = await sha256Hex(artifact?.manifest);
  const gate = artifact?.manifest?.gate;
  const checks = [
    { name: 'artifact_schema', pass: artifact?.type === 'FLOOR_PLAN_STRUCTURE_SOURCE_GATE' },
    { name: 'project_lineage', pass: artifact?.project_key === AI3D_PROJECT_KEY && artifact?.manifest?.project_key === AI3D_PROJECT_KEY },
    { name: 'gate_status_valid', pass: gate?.status === 'READY' || gate?.status === 'HOLD' },
    { name: 'no_inference_policy', pass: gate?.policy?.infer_missing_wall_endpoints === false && gate?.policy?.infer_room_dimensions_from_area === false && gate?.policy?.infer_opening_positions === false },
    { name: 'artifact_sha_readback', pass: expected === artifact?.sha256 },
  ];
  return {
    schema: 'never-tear-ai3d-floor-plan-structure-gate-qa-v1',
    status: checks.every((check) => check.pass) ? 'PASS' : 'FAIL',
    checks,
    canonical_sha256: expected,
    gate_status: gate?.status ?? 'UNKNOWN',
    gate_reasons: gate?.reasons ?? [],
  };
}
