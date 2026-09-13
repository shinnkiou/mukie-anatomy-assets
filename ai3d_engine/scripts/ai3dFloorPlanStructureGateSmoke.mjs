import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  createFloorPlanStructureGateArtifact,
  evaluateFloorPlanStructureSource,
  qaFloorPlanStructureGateArtifact,
} from '../src/floorPlanStructureGate.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const snapshotPath = path.resolve(here, '../input/walkmyplan_aacb32598eb746758d60c8_snapshot.json');
const raw = JSON.parse(await fs.readFile(snapshotPath, 'utf8'));

const currentSource = {
  ...raw.walkmyplan,
  source: 'WALKMYPLAN',
  source_role: 'MEASURED_FLOOR_PLAN_SOURCE',
};

const currentGate = evaluateFloorPlanStructureSource(currentSource);
if (currentGate.status !== 'HOLD') throw new Error('current summary-only WalkMyPlan source must HOLD');
if (!currentGate.reasons.includes('WALL_GEOMETRY_MISSING')) throw new Error('missing wall geometry was not detected');
if (!currentGate.reasons.includes('OPENING_GEOMETRY_MISSING')) throw new Error('missing opening geometry was not detected');
if (currentGate.promotion !== 'BLOCK_STRUCTURE_COMPILE') throw new Error('summary-only source must block structure compile');

const currentArtifact = await createFloorPlanStructureGateArtifact({
  source: currentSource,
  run_id: `AI3D-007-STRUCTURE-GATE-${Date.now()}`,
});
const currentQa = await qaFloorPlanStructureGateArtifact({ artifact: currentArtifact });
if (currentQa.status !== 'PASS') throw new Error('current gate artifact QA failed');

const authoritativeFixture = {
  source: 'WALKMYPLAN',
  source_role: 'MEASURED_FLOOR_PLAN_SOURCE',
  plan_id: 'fixture-plan',
  counts: { walls: 4, openings: 1, fixtures: 0, rooms: 1 },
  walls: [
    { wall_id: 1, x1: 0, y1: 0, x2: 4, y2: 0 },
    { wall_id: 2, x1: 4, y1: 0, x2: 4, y2: 3 },
    { wall_id: 3, x1: 4, y1: 3, x2: 0, y2: 3 },
    { wall_id: 4, x1: 0, y1: 3, x2: 0, y2: 0 },
  ],
  openings: [
    { opening_id: 1, kind: 'door', wall_id: 1, span_from_m: 1.5, span_to_m: 2.4 },
  ],
};
const readyGate = evaluateFloorPlanStructureSource(authoritativeFixture);
if (readyGate.status !== 'READY') throw new Error(`authoritative complete fixture must READY: ${readyGate.reasons.join(',')}`);
if (readyGate.promotion !== 'ALLOW_STRUCTURE_COMPILE') throw new Error('complete fixture must allow structure compile');

const adobeFixture = {
  ...authoritativeFixture,
  source: 'ADOBE',
  source_role: 'VISUAL_REFERENCE_ONLY',
};
const adobeGate = evaluateFloorPlanStructureSource(adobeFixture);
if (adobeGate.status !== 'HOLD' || !adobeGate.reasons.includes('NON_AUTHORITATIVE_PROVIDER')) {
  throw new Error('Adobe visual reference must never satisfy geometry source gate');
}

const incompleteOpeningFixture = {
  ...authoritativeFixture,
  openings: [{ opening_id: 1, kind: 'door', wall_id: 1 }],
};
const incompleteOpeningGate = evaluateFloorPlanStructureSource(incompleteOpeningFixture);
if (incompleteOpeningGate.status !== 'HOLD' || !incompleteOpeningGate.reasons.includes('OPENING_GEOMETRY_INCOMPLETE')) {
  throw new Error('incomplete opening geometry must HOLD');
}

const result = {
  schema: 'never-tear-ai3d-floor-plan-structure-gate-smoke-v1',
  task_id: 'AI3D-007',
  status: 'PASS',
  source_plan_id: raw.walkmyplan.plan_id,
  current_source: {
    expected_status: 'HOLD',
    actual_status: currentGate.status,
    reasons: currentGate.reasons,
    reported_counts: currentGate.counts,
    observed_geometry: currentGate.observed,
    no_invention_policy: currentGate.policy,
  },
  positive_fixture: {
    expected_status: 'READY',
    actual_status: readyGate.status,
    checks: readyGate.checks,
  },
  negative_tests: {
    adobe_visual_reference_rejected: adobeGate.status === 'HOLD',
    incomplete_opening_rejected: incompleteOpeningGate.status === 'HOLD',
  },
  artifact: {
    artifact_id: currentArtifact.artifact_id,
    sha256: currentArtifact.sha256,
    qa_status: currentQa.status,
    qa_checks: currentQa.checks,
  },
  next_action: 'Acquire authoritative full wall endpoint and opening placement geometry from the source/export path. Do not synthesize room dimensions from area or visual references.',
};

console.log(JSON.stringify(result, null, 2));
