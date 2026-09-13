import {
  compileFloorPlanStructure,
  qaCompiledFloorPlanStructure,
} from '../src/floorPlanStructureCompiler.js';

const marsSummaryOnly = {
  source: 'WALKMYPLAN',
  source_role: 'MEASURED_FLOOR_PLAN_SOURCE',
  plan_id: 'aacb32598eb746758d60c8',
  storey_height_m: 3.4,
  counts: { walls: 50, openings: 26, fixtures: 87, rooms: 14 },
};
const marsResult = await compileFloorPlanStructure(marsSummaryOnly, {
  run_id: 'AI3D-008-MARS-SOURCE-HOLD-SMOKE',
});
if (marsResult.status !== 'HOLD' || marsResult.reason !== 'SOURCE_GATE_HOLD') {
  throw new Error('summary-only Mars source must fail closed at source gate');
}
if (marsResult.production_plan !== null) throw new Error('HOLD source must not emit production commands');

const dimensionIncomplete = {
  source: 'AUTHORITATIVE_GEOMETRY',
  source_role: 'AUTHORITATIVE_GEOMETRY_SOURCE',
  storey_height_m: 3.4,
  counts: { walls: 1, openings: 0, fixtures: 0, rooms: 0 },
  walls: [{ wall_id: 1, x1: 0, y1: 0, x2: 4, y2: 0 }],
  openings: [],
};
const incompleteResult = await compileFloorPlanStructure(dimensionIncomplete, {
  run_id: 'AI3D-008-DIMENSION-HOLD-SMOKE',
});
if (incompleteResult.status !== 'HOLD' || incompleteResult.reason !== 'PHYSICAL_DIMENSIONS_INCOMPLETE') {
  throw new Error('missing wall thickness must fail closed');
}
if (!incompleteResult.missing_dimensions.includes('WALL_THICKNESS_MISSING:1')) {
  throw new Error('wall thickness blocker was not recorded');
}

const fixture = {
  source: 'AUTHORITATIVE_GEOMETRY',
  source_role: 'AUTHORITATIVE_GEOMETRY_SOURCE',
  artifact_id: 'fixture-authoritative-room-a',
  storey_height_m: 3.4,
  counts: { walls: 4, openings: 1, fixtures: 0, rooms: 1 },
  walls: [
    { wall_id: 1, x1: 0, y1: 0, x2: 4, y2: 0, thickness_m: 0.2 },
    { wall_id: 2, x1: 4, y1: 0, x2: 4, y2: 3, thickness_m: 0.2 },
    { wall_id: 3, x1: 4, y1: 3, x2: 0, y2: 3, thickness_m: 0.2 },
    { wall_id: 4, x1: 0, y1: 3, x2: 0, y2: 0, thickness_m: 0.2 },
  ],
  openings: [
    { opening_id: 10, kind: 'door', wall_id: 1, span_from_m: 1.5, span_to_m: 2.4, height_m: 2.1 },
  ],
};
const fixtureRunId = 'AI3D-008-AUTHORITATIVE-FIXTURE-SMOKE';
const first = await compileFloorPlanStructure(fixture, { run_id: fixtureRunId });
const second = await compileFloorPlanStructure(fixture, { run_id: fixtureRunId });
if (first.status !== 'PASS') throw new Error(`fixture compile failed: ${first.reason}`);
if (first.artifact.sha256 !== second.artifact.sha256) throw new Error('compiler is not deterministic');
if (first.production_plan.plan_sha256 !== second.production_plan.plan_sha256) throw new Error('production plan is not deterministic');
if (first.production_plan.commands.length !== 12) throw new Error(`expected 12 commands, got ${first.production_plan.commands.length}`);
if (first.policy.inferred_dimensions !== false || first.policy.physical_execution_claimed !== false) {
  throw new Error('compiler policy boundary violated');
}
const qa = await qaCompiledFloorPlanStructure(first);
if (qa.status !== 'PASS') throw new Error('compiled structure QA failed');

let invalidRefRejected = false;
try {
  await compileFloorPlanStructure({
    ...fixture,
    counts: { ...fixture.counts, openings: 1 },
    openings: [{ opening_id: 99, kind: 'door', wall_id: 999, span_from_m: 0.2, span_to_m: 1.1, height_m: 2.1 }],
  }, { run_id: 'AI3D-008-INVALID-WALL-REF' });
} catch (error) {
  invalidRefRejected = /missing wall/.test(String(error?.message));
}
if (!invalidRefRejected) throw new Error('invalid opening wall reference was not rejected');

let invalidSpanRejected = false;
try {
  await compileFloorPlanStructure({
    ...fixture,
    openings: [{ opening_id: 98, kind: 'door', wall_id: 1, span_from_m: 3.8, span_to_m: 4.8, height_m: 2.1 }],
  }, { run_id: 'AI3D-008-INVALID-SPAN' });
} catch (error) {
  invalidSpanRejected = /outside wall/.test(String(error?.message));
}
if (!invalidSpanRejected) throw new Error('out-of-range opening span was not rejected');

console.log(JSON.stringify({
  schema: 'never-tear-ai3d-structure-compiler-smoke-v1',
  status: 'PASS',
  evidence_class: 'SYNTHETIC_AUTHORITATIVE_FIXTURE_NOT_PHYSICAL',
  mars_source_gate: marsResult.status,
  mars_reason: marsResult.reason,
  dimension_incomplete_gate: incompleteResult.status,
  dimension_incomplete_reason: incompleteResult.reason,
  compiled_artifact_id: first.artifact.artifact_id,
  compiled_artifact_sha256: first.artifact.sha256,
  geometry_sha256: first.geometry_sha256,
  production_plan_id: first.production_plan.plan_id,
  production_plan_sha256: first.production_plan.plan_sha256,
  command_count: first.production_plan.commands.length,
  deterministic_recompile: first.artifact.sha256 === second.artifact.sha256,
  invalid_wall_reference_rejected: invalidRefRejected,
  invalid_span_rejected: invalidSpanRejected,
  qa,
  policy: first.policy,
}, null, 2));
