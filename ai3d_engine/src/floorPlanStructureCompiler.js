import {
  AI3D_PROJECT_KEY,
  sha256Hex,
  stableStringify,
  validateProductionCommand,
} from './productionProtocol.js';
import { evaluateFloorPlanStructureSource } from './floorPlanStructureGate.js';

const EPS = 1e-6;

function finitePositive(value) {
  return Number.isFinite(value) && value > 0;
}

function wallId(wall) {
  return Number.isInteger(wall?.wall_id) ? wall.wall_id : wall?.id;
}

function openingId(opening) {
  return Number.isInteger(opening?.opening_id) ? opening.opening_id : opening?.id;
}

function pointOnWallFromSpan(wall, fromM, toM) {
  const dx = wall.x2 - wall.x1;
  const dy = wall.y2 - wall.y1;
  const length = Math.hypot(dx, dy);
  if (!(fromM >= -EPS && toM <= length + EPS && toM > fromM)) {
    throw new Error(`opening span is outside wall ${wallId(wall)}`);
  }
  const centerM = (fromM + toM) / 2;
  return {
    center_xy_m: [wall.x1 + (dx / length) * centerM, wall.y1 + (dy / length) * centerM],
    width_m: toM - fromM,
    offset_m: centerM,
  };
}

function pointOnWallFromCenter(wall, center) {
  const dx = wall.x2 - wall.x1;
  const dy = wall.y2 - wall.y1;
  const length2 = dx * dx + dy * dy;
  const length = Math.sqrt(length2);
  const rx = center[0] - wall.x1;
  const ry = center[1] - wall.y1;
  const t = (rx * dx + ry * dy) / length2;
  const px = wall.x1 + t * dx;
  const py = wall.y1 + t * dy;
  const perpendicular = Math.hypot(center[0] - px, center[1] - py);
  if (t < -EPS || t > 1 + EPS || perpendicular > 1e-5) {
    throw new Error(`opening center is not on host wall ${wallId(wall)}`);
  }
  return { center_xy_m: [...center], offset_m: Math.max(0, Math.min(1, t)) * length };
}

function normalizeWall(wall, storeyHeightM) {
  const id = wallId(wall);
  const dx = wall.x2 - wall.x1;
  const dy = wall.y2 - wall.y1;
  const lengthM = Math.hypot(dx, dy);
  const angleRad = Math.atan2(dy, dx);
  const thicknessM = finitePositive(wall.thickness_m) ? wall.thickness_m : null;
  return {
    wall_id: id,
    source_endpoints_xy_m: [[wall.x1, wall.y1], [wall.x2, wall.y2]],
    length_m: lengthM,
    angle_rad: angleRad,
    midpoint_xy_m: [(wall.x1 + wall.x2) / 2, (wall.y1 + wall.y2) / 2],
    thickness_m: thicknessM,
    height_m: storeyHeightM,
    coordinate_contract: 'PLAN_XY_EAST_NORTH_TO_THREE_XZ_YUP_V1',
  };
}

function normalizeOpening(opening, wallMap) {
  const id = openingId(opening);
  const host = wallMap.get(opening.wall_id);
  if (!host) throw new Error(`opening ${id} references missing wall ${opening.wall_id}`);
  const placement = Number.isFinite(opening.span_from_m) && Number.isFinite(opening.span_to_m)
    ? pointOnWallFromSpan(host, opening.span_from_m, opening.span_to_m)
    : pointOnWallFromCenter(host, opening.center_xy_m);
  const widthM = finitePositive(opening.width_m) ? opening.width_m : placement.width_m ?? null;
  const sillM = opening.kind === 'door'
    ? Number.isFinite(opening.sill_height_m) ? opening.sill_height_m : 0
    : Number.isFinite(opening.sill_height_m) ? opening.sill_height_m : null;
  const heightM = finitePositive(opening.height_m) ? opening.height_m : null;
  return {
    opening_id: id,
    kind: opening.kind,
    wall_id: opening.wall_id,
    center_xy_m: placement.center_xy_m,
    offset_m: placement.offset_m,
    width_m: widthM,
    sill_height_m: sillM,
    height_m: heightM,
    vertical_profile_complete: finitePositive(widthM) && Number.isFinite(sillM) && finitePositive(heightM),
  };
}

function sourceArtifactIds(source) {
  const refs = [];
  if (typeof source.artifact_id === 'string' && source.artifact_id) refs.push(source.artifact_id);
  if (source.plan_id) refs.push(`walkmyplan:${source.plan_id}`);
  return refs;
}

function commandLineage(source, moduleId) {
  return { source_artifact_ids: sourceArtifactIds(source), module_id: moduleId };
}

function buildWallCommands(wall, source) {
  const name = `wall_${wall.wall_id}`;
  return [
    {
      command_id: `wall-${wall.wall_id}-create`,
      op: 'CREATE_PRIMITIVE',
      params: {
        name,
        kind: 'box',
        position: [wall.midpoint_xy_m[0], wall.height_m / 2, wall.midpoint_xy_m[1]],
        size: [wall.length_m, wall.height_m, wall.thickness_m],
      },
      lineage: commandLineage(source, `wall:${wall.wall_id}`),
      routes: ['WEBGL', 'WINDOWS_WORKER'],
    },
    {
      command_id: `wall-${wall.wall_id}-rotate`,
      op: 'TRANSFORM_SET',
      params: { name, rotation: [0, -wall.angle_rad, 0] },
      lineage: commandLineage(source, `wall:${wall.wall_id}`),
      routes: ['WEBGL', 'WINDOWS_WORKER'],
    },
  ];
}

function buildOpeningCommands(opening, wall, source) {
  const cutter = `opening_cutter_${opening.opening_id}`;
  const target = `wall_${opening.wall_id}`;
  const cutterDepth = wall.thickness_m + 0.02;
  return [
    {
      command_id: `opening-${opening.opening_id}-create-cutter`,
      op: 'CREATE_PRIMITIVE',
      params: {
        name: cutter,
        kind: 'box',
        position: [opening.center_xy_m[0], opening.sill_height_m + opening.height_m / 2, opening.center_xy_m[1]],
        size: [opening.width_m, opening.height_m, cutterDepth],
      },
      lineage: commandLineage(source, `opening:${opening.opening_id}`),
      routes: ['WEBGL', 'WINDOWS_WORKER'],
    },
    {
      command_id: `opening-${opening.opening_id}-rotate-cutter`,
      op: 'TRANSFORM_SET',
      params: { name: cutter, rotation: [0, -wall.angle_rad, 0] },
      lineage: commandLineage(source, `opening:${opening.opening_id}`),
      routes: ['WEBGL', 'WINDOWS_WORKER'],
    },
    {
      command_id: `opening-${opening.opening_id}-boolean`,
      op: 'BOOLEAN',
      params: { target, tool: cutter, mode: 'subtract', keep_tool: false },
      lineage: commandLineage(source, `opening:${opening.opening_id}`),
      routes: ['WEBGL', 'WINDOWS_WORKER'],
    },
  ];
}

export async function compileFloorPlanStructure(source, { task_id = 'AI3D-008', run_id = 'AI3D-008-STRUCTURE-COMPILE' } = {}) {
  const sourceGate = evaluateFloorPlanStructureSource(source);
  if (sourceGate.status !== 'READY') {
    return {
      schema: 'never-tear-ai3d-structure-compiler-result-v1',
      project_key: AI3D_PROJECT_KEY,
      task_id,
      run_id,
      status: 'HOLD',
      reason: 'SOURCE_GATE_HOLD',
      source_gate: sourceGate,
      production_plan: null,
      policy: { inferred_dimensions: false, physical_execution_claimed: false },
    };
  }

  const storeyHeightM = finitePositive(source.storey_height_m) ? source.storey_height_m : null;
  const sourceWalls = [...source.walls].sort((a, b) => wallId(a) - wallId(b));
  const wallMap = new Map(sourceWalls.map((wall) => [wallId(wall), wall]));
  const walls = sourceWalls.map((wall) => normalizeWall(wall, storeyHeightM));
  const openings = [...source.openings]
    .sort((a, b) => openingId(a) - openingId(b))
    .map((opening) => normalizeOpening(opening, wallMap));

  const missingDimensions = [];
  if (!storeyHeightM) missingDimensions.push('STOREY_HEIGHT_MISSING');
  for (const wall of walls) if (!finitePositive(wall.thickness_m)) missingDimensions.push(`WALL_THICKNESS_MISSING:${wall.wall_id}`);
  for (const opening of openings) if (!opening.vertical_profile_complete) missingDimensions.push(`OPENING_PROFILE_INCOMPLETE:${opening.opening_id}`);

  const geometry = {
    coordinate_contract: 'PLAN_XY_EAST_NORTH_TO_THREE_XZ_YUP_V1',
    storey_height_m: storeyHeightM,
    walls,
    openings,
    counts: { walls: walls.length, openings: openings.length },
  };
  const geometry_sha256 = await sha256Hex(geometry);

  if (missingDimensions.length) {
    return {
      schema: 'never-tear-ai3d-structure-compiler-result-v1',
      project_key: AI3D_PROJECT_KEY,
      task_id,
      run_id,
      status: 'HOLD',
      reason: 'PHYSICAL_DIMENSIONS_INCOMPLETE',
      missing_dimensions: missingDimensions,
      source_gate: sourceGate,
      geometry,
      geometry_sha256,
      production_plan: null,
      policy: { inferred_dimensions: false, physical_execution_claimed: false },
    };
  }

  const normalizedWallMap = new Map(walls.map((wall) => [wall.wall_id, wall]));
  const commands = [];
  for (const wall of walls) commands.push(...buildWallCommands(wall, source));
  for (const opening of openings) commands.push(...buildOpeningCommands(opening, normalizedWallMap.get(opening.wall_id), source));
  commands.push({
    command_id: 'structure-qa',
    op: 'QA_RUN',
    params: { checks: ['wall_count', 'opening_count', 'source_lineage', 'no_inferred_dimensions'] },
    lineage: commandLineage(source, 'floor-plan-structure'),
    routes: ['WEBGL', 'WINDOWS_WORKER'],
  });
  for (const command of commands) validateProductionCommand(command);

  const planCore = {
    schema: 'never-tear-ai3d-structure-production-plan-v1',
    project_key: AI3D_PROJECT_KEY,
    task_id,
    run_id,
    coordinate_contract: geometry.coordinate_contract,
    source_geometry_sha256: geometry_sha256,
    commands,
  };
  const plan_sha256 = await sha256Hex(planCore);
  const production_plan = {
    ...planCore,
    plan_id: `structure-plan-${plan_sha256.slice(0, 16)}`,
    plan_sha256,
  };

  const manifest = {
    schema: 'never-tear-ai3d-structure-compiler-artifact-v1',
    project_key: AI3D_PROJECT_KEY,
    task_id,
    run_id,
    source_provider: sourceGate.provider,
    source_role: sourceGate.source_role,
    source_refs: sourceArtifactIds(source),
    geometry,
    geometry_sha256,
    production_plan,
    policy: {
      inferred_dimensions: false,
      room_area_reconstruction: false,
      footprint_reconstruction: false,
      total_wall_length_reconstruction: false,
      adobe_geometry_truth: false,
      failed_to3d_geometry_truth: false,
      physical_execution_claimed: false,
    },
  };
  const artifact_sha256 = await sha256Hex(manifest);
  return {
    schema: 'never-tear-ai3d-structure-compiler-result-v1',
    project_key: AI3D_PROJECT_KEY,
    task_id,
    run_id,
    status: 'PASS',
    reason: null,
    source_gate: sourceGate,
    geometry,
    geometry_sha256,
    production_plan,
    artifact: {
      artifact_id: `structure-compile-${artifact_sha256.slice(0, 16)}`,
      type: 'FLOOR_PLAN_STRUCTURE_COMPILE',
      sha256: artifact_sha256,
      manifest,
      canonical_json: stableStringify(manifest),
    },
    policy: manifest.policy,
  };
}

export async function qaCompiledFloorPlanStructure(result) {
  const checks = [];
  checks.push({ name: 'status_pass', pass: result?.status === 'PASS' });
  checks.push({ name: 'source_gate_ready', pass: result?.source_gate?.status === 'READY' });
  checks.push({ name: 'no_inferred_dimensions', pass: result?.policy?.inferred_dimensions === false });
  checks.push({ name: 'physical_not_claimed', pass: result?.policy?.physical_execution_claimed === false });
  if (result?.status === 'PASS') {
    const expectedArtifactSha = await sha256Hex(result.artifact.manifest);
    const expectedGeometrySha = await sha256Hex(result.geometry);
    const expectedPlanSha = await sha256Hex({
      schema: result.production_plan.schema,
      project_key: result.production_plan.project_key,
      task_id: result.production_plan.task_id,
      run_id: result.production_plan.run_id,
      coordinate_contract: result.production_plan.coordinate_contract,
      source_geometry_sha256: result.production_plan.source_geometry_sha256,
      commands: result.production_plan.commands,
    });
    checks.push({ name: 'artifact_sha_readback', pass: expectedArtifactSha === result.artifact.sha256 });
    checks.push({ name: 'geometry_sha_readback', pass: expectedGeometrySha === result.geometry_sha256 });
    checks.push({ name: 'plan_sha_readback', pass: expectedPlanSha === result.production_plan.plan_sha256 });
    checks.push({ name: 'commands_validate', pass: result.production_plan.commands.every((command) => Boolean(validateProductionCommand(command))) });
  }
  return {
    schema: 'never-tear-ai3d-structure-compiler-qa-v1',
    status: checks.every((check) => check.pass) ? 'PASS' : 'FAIL',
    checks,
  };
}
