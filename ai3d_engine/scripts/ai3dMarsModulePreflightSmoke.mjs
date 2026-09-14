import fs from 'node:fs';
import path from 'node:path';
import {
  compileFloorPlanStructure,
} from '../src/floorPlanStructureCompiler.js';
import {
  AI3D_PROJECT_KEY,
  sha256Hex,
  stableStringify,
  validateProductionCommand,
} from '../src/productionProtocol.js';

const authorityPath = new URL('../data/walkmyplan_revision380_geometry_recovery.json', import.meta.url);
const manifestPath = new URL('../data/mars_structure_module_execution_v1.json', import.meta.url);
const authority = JSON.parse(fs.readFileSync(authorityPath, 'utf8'));
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const outDir = process.argv[2] || 'ai3d_engine/artifacts/mars_module_preflight';
fs.mkdirSync(outDir, { recursive: true });

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(manifest.schema === 'never-tear-ai3d-mars-structure-module-execution-v1', 'unexpected module manifest schema');
assert(manifest.status === 'READY_WAITING_PHYSICAL_GATE', 'module manifest must remain waiting on physical gate');
assert(manifest.source_authority?.plan_id === authority.plan_id, 'plan id drift between module manifest and authority');
assert(manifest.source_authority?.structure_geometry_revision === authority.revision, 'authority revision drift');
assert(manifest.source_authority?.geometry_sha256 === '0efa7547c1e065304d93eb5fb0cc858e668c41c3bc6516d0b7ab84302f6f52fb', 'unexpected geometry authority sha');
assert(manifest.source_authority?.whole_plan_command_count === 179, 'whole Mars Structure plan must remain 179 commands');
assert(manifest.source_authority?.geometry_research_closed === true, 'geometry research must remain closed');
assert(manifest.physical_gate?.required_capability === 'ai3d_blender_physical_mvp_v1', 'wrong physical capability gate');
assert(manifest.physical_gate?.legacy_worker_ineligible === '0.18.2-p0.18.2 / ukie_worker_v1', 'legacy worker boundary changed');
assert(manifest.physical_gate?.current_state === 'BLOCKED_CAPABILITY_NOT_ADVERTISED', 'preflight may not claim physical capability');
assert(manifest.physical_gate?.queued_jobs === 0, 'no AI3D job may be queued during preflight');

const central = manifest.modules.find((module) => module.module_id === 'central_corridor_structure_base');
const blast = manifest.modules.find((module) => module.module_id === 'blast_junction_damage_overlay');
assert(central, 'central corridor module missing');
assert(blast, 'blast junction module missing');
assert(central.stage === 'READY_WAITING_PHYSICAL_GATE', 'central corridor must remain waiting on physical gate');
assert(blast.stage === 'READY_AFTER_CENTRAL_CORRIDOR_STRUCTURE_QA', 'blast junction dependency boundary changed');

const authorityWalls = new Map(authority.walls.map((wall) => [wall.id, wall]));
const authorityOpenings = new Map(authority.openings.map((opening) => [opening.id, opening]));
const centralWallIds = new Set(central.wall_ids);
const centralOpeningIds = new Set(central.opening_ids);

assert(centralWallIds.size === central.wall_ids.length && central.wall_ids.length === 13, 'central corridor wall IDs must be 13 unique values');
assert(centralOpeningIds.size === central.opening_ids.length && central.opening_ids.length === 13, 'central corridor opening IDs must be 13 unique values');
for (const id of central.wall_ids) assert(authorityWalls.has(id), `central corridor wall ${id} missing from authority`);
for (const id of central.opening_ids) {
  const opening = authorityOpenings.get(id);
  assert(opening, `central corridor opening ${id} missing from authority`);
  assert(centralWallIds.has(opening.wall_id), `opening ${id} host wall ${opening.wall_id} not inside central corridor wall set`);
}
assert(central.compiler_command_subset_count === central.wall_ids.length * 2 + central.opening_ids.length * 3, 'declared central corridor command subset count is inconsistent');

const [minX, maxX] = central.plan_bbox_xy_m.x;
const [minY, maxY] = central.plan_bbox_xy_m.y;
for (const id of central.wall_ids) {
  const wall = authorityWalls.get(id);
  for (const [x, y] of [[wall.x1, wall.y1], [wall.x2, wall.y2]]) {
    assert(x >= minX && x <= maxX && y >= minY && y <= maxY, `wall ${id} endpoint outside module bbox`);
  }
}
for (const id of central.opening_ids) {
  const [x, y] = authorityOpenings.get(id).center_xy_m;
  assert(x >= minX && x <= maxX && y >= minY && y <= maxY, `opening ${id} center outside module bbox`);
}

assert(central.connection_sockets.length === central.opening_ids.length, 'connection sockets must cover every central corridor opening');
const socketOpeningIds = new Set();
for (const socket of central.connection_sockets) {
  assert(centralOpeningIds.has(socket.opening_id), `socket ${socket.socket_id} references opening outside central corridor`);
  assert(!socketOpeningIds.has(socket.opening_id), `duplicate socket for opening ${socket.opening_id}`);
  socketOpeningIds.add(socket.opening_id);
  const opening = authorityOpenings.get(socket.opening_id);
  assert(socket.plan_xy_m[0] === opening.center_xy_m[0] && socket.plan_xy_m[1] === opening.center_xy_m[1], `socket ${socket.socket_id} coordinate drift`);
}

for (const id of blast.primary_source_wall_ids) assert(centralWallIds.has(id), `blast wall ${id} must be part of central corridor base`);
for (const id of blast.critical_opening_ids) assert(centralOpeningIds.has(id), `blast opening ${id} must be part of central corridor base`);
assert(blast.existing_asset_carryover?.known_prefixes?.includes('DMG024_'), 'blast damage carryover prefix missing');
assert(blast.existing_asset_carryover?.known_prefixes?.includes('HERO_BLAST_'), 'blast hero carryover prefix missing');
assert(blast.damage_policy?.uniform_random_damage === false, 'uniform random blast damage is forbidden');
assert(blast.damage_policy?.whole_base_blackening === false, 'whole-base blackening is forbidden');

const full = await compileFloorPlanStructure(authority, {
  task_id: 'AI3D-009',
  run_id: 'AI3D-009-WALKMYPLAN-REV380-RECOVERY-CANDIDATE',
});
assert(full.status === 'PASS', `authority compile failed: ${full.reason}`);
assert(full.geometry_sha256 === manifest.source_authority.geometry_sha256, 'compiled geometry sha drift');
assert(full.production_plan.plan_id === manifest.source_authority.production_plan_id, 'authoritative production plan id drift');
assert(full.production_plan.plan_sha256 === manifest.source_authority.production_plan_sha256, 'authoritative production plan sha drift');
assert(full.production_plan.commands.length === 179, 'authoritative production plan command count drift');

const wantedLineage = new Set([
  ...central.wall_ids.map((id) => `wall:${id}`),
  ...central.opening_ids.map((id) => `opening:${id}`),
]);
const subset = full.production_plan.commands.filter((command) => wantedLineage.has(command.lineage?.module_id));
assert(subset.length === 65, `expected 65 central corridor geometry commands, got ${subset.length}`);
assert(new Set(subset.map((command) => command.command_id)).size === subset.length, 'duplicate command id in central corridor subset');
for (const command of subset) validateProductionCommand(command);

const expectedCommandIds = new Set([
  ...central.wall_ids.flatMap((id) => [`wall-${id}-create`, `wall-${id}-rotate`]),
  ...central.opening_ids.flatMap((id) => [`opening-${id}-create-cutter`, `opening-${id}-rotate-cutter`, `opening-${id}-boolean`]),
]);
assert(expectedCommandIds.size === 65, 'expected command-id set must contain 65 commands');
for (const id of expectedCommandIds) assert(subset.some((command) => command.command_id === id), `missing compiled command ${id}`);

const moduleQaCommand = validateProductionCommand({
  command_id: 'central-corridor-module-qa',
  op: 'QA_RUN',
  params: {
    checks: [
      'source_wall_opening_ids_exact',
      'walkmyplan_coordinate_alignment',
      'door_openings_unobstructed',
      'floor_contact_and_wall_continuity',
      'existing_corridor_assets_preserved',
      'no_inferred_dimensions',
    ],
  },
  lineage: {
    source_artifact_ids: [`walkmyplan:${authority.plan_id}@revision${authority.revision}`, full.artifact.artifact_id],
    module_id: 'central_corridor_structure_base',
  },
  routes: ['WEBGL', 'WINDOWS_WORKER'],
});

const planCore = {
  schema: 'never-tear-ai3d-module-production-plan-v1',
  project_key: AI3D_PROJECT_KEY,
  task_id: 'AI3D-010',
  run_id: 'AI3D-010-CENTRAL-CORRIDOR-STRUCTURE-PREFLIGHT',
  module_id: 'central_corridor_structure_base',
  coordinate_contract: full.production_plan.coordinate_contract,
  source_geometry_sha256: full.geometry_sha256,
  source_production_plan_id: full.production_plan.plan_id,
  source_production_plan_sha256: full.production_plan.plan_sha256,
  commands: [...subset, moduleQaCommand],
  policy: {
    geometry_mutated: false,
    inferred_dimensions: false,
    physical_execution_claimed: false,
    legacy_worker_eligible: false,
  },
};
const planSha256 = await sha256Hex(planCore);
const modulePlan = {
  ...planCore,
  plan_id: `module-plan-${planSha256.slice(0, 16)}`,
  plan_sha256: planSha256,
};

const evidenceCore = {
  schema: 'never-tear-ai3d-module-production-preflight-qa-v1',
  project_key: AI3D_PROJECT_KEY,
  task_id: 'AI3D-010',
  status: 'PASS',
  evidence_class: 'PREFLIGHT_LOGIC_ONLY_NOT_PHYSICAL',
  source_authority: {
    plan_id: authority.plan_id,
    revision: authority.revision,
    geometry_sha256: full.geometry_sha256,
    production_plan_id: full.production_plan.plan_id,
    production_plan_sha256: full.production_plan.plan_sha256,
  },
  module: {
    module_id: central.module_id,
    wall_count: central.wall_ids.length,
    opening_count: central.opening_ids.length,
    geometry_command_count: subset.length,
    qa_command_count: 1,
    execution_command_count: modulePlan.commands.length,
    connection_socket_count: central.connection_sockets.length,
  },
  blast_overlay_dependency: {
    module_id: blast.module_id,
    base_module: blast.base_module,
    primary_source_wall_ids: blast.primary_source_wall_ids,
    critical_opening_ids: blast.critical_opening_ids,
    existing_assets_reused: true,
  },
  module_plan_id: modulePlan.plan_id,
  module_plan_sha256: modulePlan.plan_sha256,
  checks: {
    exact_authority_ids: true,
    exact_socket_coordinates: true,
    exact_compiler_subset: true,
    no_duplicate_commands: true,
    blast_overlay_is_subset_of_base: true,
    geometry_research_closed: true,
    physical_gate_preserved: true,
    physical_execution_claimed: false,
  },
  next_action: 'Keep AI3D-010 READY. Queue no production job until AI3D-002 verified companion advertises ai3d_blender_physical_mvp_v1 and AI3D-004 real Physical QA passes. Then execute this Central Corridor module plan before Blast Junction overlay integration.',
};
const evidenceSha256 = await sha256Hex(evidenceCore);
const evidence = {
  ...evidenceCore,
  evidence_sha256: evidenceSha256,
};

fs.writeFileSync(path.join(outDir, 'central_corridor_module_plan.json'), JSON.stringify(modulePlan, null, 2) + '\n');
fs.writeFileSync(path.join(outDir, 'module_preflight_qa.json'), JSON.stringify(evidence, null, 2) + '\n');
fs.writeFileSync(path.join(outDir, 'module_preflight_canonical.json'), stableStringify(evidence) + '\n');
console.log(JSON.stringify(evidence, null, 2));
