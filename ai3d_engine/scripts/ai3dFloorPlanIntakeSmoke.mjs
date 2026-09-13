import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { createExternalFloorPlanIntakeArtifact, qaExternalFloorPlanIntake } from '../src/externalFloorPlanIntake.js';

const inputPath = fileURLToPath(new URL('../input/walkmyplan_aacb32598eb746758d60c8_snapshot.json', import.meta.url));
const input = JSON.parse(fs.readFileSync(inputPath, 'utf8'));

const artifact = await createExternalFloorPlanIntakeArtifact({
  walkmyplan: input.walkmyplan,
  adobe_assets: input.adobe_assets,
  to3d_job: input.to3d_job,
  task_id: 'AI3D-006',
  run_id: 'AI3D-006-WALKMYPLAN-INTAKE-SMOKE',
});
const qa = await qaExternalFloorPlanIntake({ artifact });

if (qa.status !== 'PASS') throw new Error(`AI3D-006 intake QA failed: ${JSON.stringify(qa.checks)}`);
if (artifact.manifest.modules.length !== 14) throw new Error('Expected 14 room modules');
if (artifact.manifest.source.counts.walls !== 50) throw new Error('Expected 50 walls in source summary');
if (artifact.manifest.source.counts.openings !== 26) throw new Error('Expected 26 openings in source summary');
if (artifact.manifest.source.counts.fixtures !== 87) throw new Error('Expected 87 fixtures in source summary');
if (artifact.manifest.source.storey_height_m !== 3.4) throw new Error('Expected 3.4m storey height');
if (artifact.manifest.references.adobe.length !== 6) throw new Error('Expected 6 Adobe references');
if (!artifact.manifest.references.adobe.every((a) => a.canonical === false && a.eligible_for_geometry_truth === false)) throw new Error('Adobe boundary failed');
if (artifact.manifest.references.to3d.retry_policy !== 'NO_RETRY' || artifact.manifest.references.to3d.eligible_for_import !== false) throw new Error('to3D failed-job boundary failed');

const room0 = artifact.manifest.modules.find((m) => m.metadata.source_room_id === 0);
if (!room0 || room0.metadata.source_room_name !== '大型ハンガー' || room0.metadata.measured_area_m2 !== 163.6) throw new Error('Room 0 mapping failed');

process.stdout.write(JSON.stringify({
  schema: 'never-tear-ai3d-external-floor-plan-intake-smoke-v1',
  status: 'PASS',
  task_id: 'AI3D-006',
  artifact_id: artifact.artifact_id,
  artifact_sha256: artifact.sha256,
  module_count: artifact.manifest.modules.length,
  source_plan_id: artifact.manifest.source.plan_id,
  source_counts: artifact.manifest.source.counts,
  storey_height_m: artifact.manifest.source.storey_height_m,
  adobe_reference_count: artifact.manifest.references.adobe.length,
  adobe_boundary: 'NON_CANONICAL_VISUAL_REFERENCE',
  to3d_job_status: artifact.manifest.references.to3d.status,
  to3d_retry_policy: artifact.manifest.references.to3d.retry_policy,
  qa,
}, null, 2));
