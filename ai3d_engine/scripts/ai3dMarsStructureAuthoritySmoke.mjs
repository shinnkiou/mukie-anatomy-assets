import fs from 'node:fs';
import path from 'node:path';
import {
  compileFloorPlanStructure,
  qaCompiledFloorPlanStructure,
} from '../src/floorPlanStructureCompiler.js';

const sourcePath = new URL('../data/walkmyplan_revision380_geometry_recovery.json', import.meta.url);
const source = JSON.parse(fs.readFileSync(sourcePath, 'utf8'));
const outDir = process.argv[2] || 'ai3d_engine/artifacts/mars_structure_authority';
fs.mkdirSync(outDir, { recursive: true });

if (source.plan_id !== 'aacb32598eb746758d60c8' || source.revision !== 380) {
  throw new Error('unexpected WalkMyPlan authority source');
}
if (source.walls.length !== 50 || source.openings.length !== 26) {
  throw new Error('authority source must contain exactly 50 walls and 26 openings');
}
if (source.authority_separation?.room_registry_authority?.room_count !== 14) {
  throw new Error('current 14-room Module Registry authority was not preserved');
}
if (source.authority_separation?.historical_room_snapshot?.room_count !== 15
  || source.authority_separation?.historical_room_snapshot?.authoritative_for_current_room_registry !== false) {
  throw new Error('historical 15-room snapshot boundary is not explicit');
}
if (source.revision_history_check?.wall_or_opening_edit_count !== 0
  || source.revision_history_check?.revisions_381_to_423_observed_no_wall_or_opening_edit_in_revision_log !== true) {
  throw new Error('revision-drift proof is incomplete');
}

const totalWallLengthM = source.walls.reduce((sum, wall) => sum + Math.hypot(wall.x2 - wall.x1, wall.y2 - wall.y1), 0);
const xs = source.walls.flatMap((wall) => [wall.x1, wall.x2]);
const ys = source.walls.flatMap((wall) => [wall.y1, wall.y2]);
const footprintM = [Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)];
const aggregate = source.current_aggregate_readback;
if (Math.abs(totalWallLengthM - aggregate.total_wall_length_m) > 1e-9) {
  throw new Error(`wall length mismatch: ${totalWallLengthM} != ${aggregate.total_wall_length_m}`);
}
if (Math.abs(footprintM[0] - aggregate.footprint_m[0]) > 1e-9 || Math.abs(footprintM[1] - aggregate.footprint_m[1]) > 1e-9) {
  throw new Error(`footprint mismatch: ${footprintM} != ${aggregate.footprint_m}`);
}
if (aggregate.walls !== 50 || aggregate.openings !== 26 || aggregate.rooms !== 14 || aggregate.fixtures !== 87) {
  throw new Error('current aggregate authority snapshot is unexpected');
}

const runId = 'AI3D-009-WALKMYPLAN-REV380-RECOVERY-CANDIDATE';
const first = await compileFloorPlanStructure(source, { task_id: 'AI3D-009', run_id: runId });
const second = await compileFloorPlanStructure(source, { task_id: 'AI3D-009', run_id: runId });
if (first.status !== 'PASS') throw new Error(`Mars Structure compile failed: ${first.reason}`);
if (first.source_gate?.status !== 'READY') throw new Error('Structure Source Gate did not promote to READY');
if (first.production_plan.commands.length !== 179) throw new Error(`expected 179 commands, got ${first.production_plan.commands.length}`);
if (first.artifact.sha256 !== second.artifact.sha256 || first.production_plan.plan_sha256 !== second.production_plan.plan_sha256) {
  throw new Error('Mars Structure compile is not deterministic');
}
const qa = await qaCompiledFloorPlanStructure(first);
if (qa.status !== 'PASS') throw new Error('Mars Structure compiler QA failed');
if (first.policy.inferred_dimensions !== false || first.policy.physical_execution_claimed !== false) {
  throw new Error('authority compile violated no-inference / non-physical boundary');
}

const expected = {
  geometry_sha256: '0efa7547c1e065304d93eb5fb0cc858e668c41c3bc6516d0b7ab84302f6f52fb',
  plan_id: 'structure-plan-83389de2d8016fb6',
  plan_sha256: '83389de2d8016fb6dc1ec043befd071d8c937b162c6dbf479a9d19582b3e5313',
  artifact_id: 'structure-compile-9453eb39e916c096',
  artifact_sha256: '9453eb39e916c096bfd1e0355bd92070e350cd1f69858da5aafec11d953f6465',
};
for (const [key, value] of Object.entries(expected)) {
  const actual = key === 'geometry_sha256' ? first.geometry_sha256
    : key === 'plan_id' ? first.production_plan.plan_id
    : key === 'plan_sha256' ? first.production_plan.plan_sha256
    : key === 'artifact_id' ? first.artifact.artifact_id
    : first.artifact.sha256;
  if (actual !== value) throw new Error(`${key} changed: ${actual} != ${value}`);
}

const evidence = {
  schema: 'never-tear-ai3d-mars-structure-geometry-authority-qa-v1',
  project_key: 'never_tear_ai3d_engine',
  task_id: 'AI3D-009',
  status: 'PASS',
  promotion: 'STRUCTURE_GEOMETRY_AUTHORITY_PROMOTED',
  source_provider: 'WALKMYPLAN',
  plan_id: source.plan_id,
  source_revision: source.revision,
  revision_drift_proof: {
    checked_range: source.revision_history_check.range,
    revisions_checked: source.revision_history_check.revision_count,
    wall_or_opening_edits: source.revision_history_check.wall_or_opening_edit_count,
    post_380_fixture_additions: source.revision_history_check.post_380_fixture_additions,
  },
  authority_separation: source.authority_separation,
  aggregate_match: {
    wall_count: source.walls.length,
    opening_count: source.openings.length,
    total_wall_length_m: totalWallLengthM,
    footprint_m: footprintM,
    current_room_count: aggregate.rooms,
    current_fixture_count: aggregate.fixtures,
    status: 'PASS',
  },
  structure_source_gate: first.source_gate.status,
  compiler_status: first.status,
  compiler_qa: qa,
  geometry_sha256: first.geometry_sha256,
  production_plan_id: first.production_plan.plan_id,
  production_plan_sha256: first.production_plan.plan_sha256,
  compiled_artifact_id: first.artifact.artifact_id,
  compiled_artifact_sha256: first.artifact.sha256,
  command_count: first.production_plan.commands.length,
  deterministic_recompile: true,
  evidence_class: 'AUTHORITATIVE_MARS_GEOMETRY_COMPILE_NOT_PHYSICAL',
  policy: {
    inferred_dimensions: false,
    room_registry_replaced: false,
    historical_room_topology_promoted: false,
    physical_execution_claimed: false,
  },
  next_action: 'AI3D-009 COMPLETE. Keep the 14-room AI3D-006 Module Registry as current room authority. Next primary gate is AI3D-002: verified separate Windows companion must advertise ai3d_blender_physical_mvp_v1 before exactly one physical CANARY.',
};

fs.writeFileSync(path.join(outDir, 'authority_qa.json'), JSON.stringify(evidence, null, 2) + '\n');
fs.writeFileSync(path.join(outDir, 'mars_structure_plan.json'), JSON.stringify(first.production_plan, null, 2) + '\n');
fs.writeFileSync(path.join(outDir, 'mars_structure_compiler_artifact.json'), JSON.stringify(first.artifact, null, 2) + '\n');
console.log(JSON.stringify(evidence, null, 2));
