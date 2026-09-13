import fs from 'node:fs/promises';
import path from 'node:path';
import {
  AI3D_PROJECT_KEY,
  createCheckpointRecord,
  executeProductionPlan,
  sha256Hex,
} from '../src/productionProtocol.js';

const outDir = path.resolve('artifacts/ai3d_lineage');
await fs.mkdir(outDir, { recursive: true });

const lineage = {
  parent_artifact_id: 'artifact-parent-ai3d003',
  source_artifact_ids: ['artifact-source-a', 'artifact-source-b'],
  module_id: 'module-ai3d003-smoke',
};

const renderParams = {
  name: 'ai3d-003-lineage-preview',
  camera: 'three-quarter',
  width: 640,
  height: 360,
};

const plan = {
  plan_id: `AI3D-003-LINEAGE-${Date.now()}`,
  task_id: 'AI3D-003',
  commands: [
    {
      command_id: 'AI3D-003-C01',
      op: 'CREATE_PRIMITIVE',
      params: { kind: 'box', name: 'Lineage_Box', size: [1, 2, 3], position: [0, 0.5, 0] },
      routes: ['VIRTUAL_WORKER'],
    },
    {
      command_id: 'AI3D-003-C02',
      op: 'RENDER_CAPTURE',
      params: renderParams,
      lineage,
      routes: ['VIRTUAL_WORKER'],
    },
    {
      command_id: 'AI3D-003-C03',
      op: 'QA_RUN',
      params: { checks: [{ type: 'lineage_complete' }] },
      routes: ['VIRTUAL_WORKER'],
    },
    {
      command_id: 'AI3D-003-C04',
      op: 'CHECKPOINT_SAVE',
      params: { name: 'ai3d-003-lineage-pass' },
      routes: ['VIRTUAL_WORKER'],
    },
  ],
};

const adapter = {
  async run(command, route, state) {
    if (route !== 'VIRTUAL_WORKER') return { status: 'FAILED', error: `route unavailable: ${route}` };

    if (command.op === 'CREATE_PRIMITIVE') {
      return {
        status: 'PASS',
        object: {
          name: command.params.name,
          kind: command.params.kind,
          size: command.params.size,
          position: command.params.position,
          rotation: [0, 0, 0],
          scale: [1, 1, 1],
        },
      };
    }

    if (command.op === 'RENDER_CAPTURE') {
      const payload = {
        renderer: 'virtual-worker-lineage-smoke',
        camera: command.params.camera,
        width: command.params.width,
        height: command.params.height,
        objects: state.objects,
      };
      const sha256 = await sha256Hex(payload);
      return {
        status: 'PASS',
        artifact: {
          artifact_id: `lineage-render-${sha256.slice(0, 16)}`,
          type: 'RENDER_EVIDENCE',
          sha256,
          created_at: new Date().toISOString(),
          metadata: payload,
        },
      };
    }

    if (command.op === 'QA_RUN') {
      const artifact = state.artifacts.at(-1);
      const expectedParamsSha = await sha256Hex(renderParams);
      const pass = Boolean(artifact)
        && artifact.project_key === AI3D_PROJECT_KEY
        && artifact.task_id === 'AI3D-003'
        && artifact.run_id === plan.plan_id
        && artifact.command_id === 'AI3D-003-C02'
        && artifact.operation === 'RENDER_CAPTURE'
        && artifact.route === 'VIRTUAL_WORKER'
        && artifact.parent_artifact_id === lineage.parent_artifact_id
        && JSON.stringify(artifact.source_artifact_ids) === JSON.stringify(lineage.source_artifact_ids)
        && artifact.module_id === lineage.module_id
        && artifact.params_sha256 === expectedParamsSha;
      return {
        status: 'PASS',
        qa: {
          qa_id: `qa-lineage-${Date.now()}`,
          status: pass ? 'PASS' : 'FAIL',
          checks: [{ type: 'lineage_complete', pass }],
          created_at: new Date().toISOString(),
        },
      };
    }

    if (command.op === 'CHECKPOINT_SAVE') {
      const checkpoint = await createCheckpointRecord(state, command.params.name, {
        scope: 'ai3d-003-lineage-smoke',
        lineage_fields_verified: [
          'project_key',
          'task_id',
          'run_id',
          'command_id',
          'operation',
          'route',
          'parent_artifact_id',
          'source_artifact_ids',
          'module_id',
          'params_sha256',
        ],
      });
      return { status: 'PASS', checkpoint };
    }

    return { status: 'FAILED', error: `adapter does not implement ${command.op}` };
  },
};

const state = await executeProductionPlan({ plan, adapter });
const artifact = state.artifacts.at(-1);
const expectedParamsSha256 = await sha256Hex(renderParams);
const pass = state.status === 'PASS'
  && state.qa_reports.at(-1)?.status === 'PASS'
  && state.checkpoints.length === 1
  && artifact?.project_key === AI3D_PROJECT_KEY
  && artifact?.task_id === 'AI3D-003'
  && artifact?.run_id === plan.plan_id
  && artifact?.command_id === 'AI3D-003-C02'
  && artifact?.operation === 'RENDER_CAPTURE'
  && artifact?.route === 'VIRTUAL_WORKER'
  && artifact?.parent_artifact_id === lineage.parent_artifact_id
  && JSON.stringify(artifact?.source_artifact_ids) === JSON.stringify(lineage.source_artifact_ids)
  && artifact?.module_id === lineage.module_id
  && artifact?.params_sha256 === expectedParamsSha256;

const result = {
  schema: 'never-tear-ai3d-lineage-smoke-v1',
  project_key: AI3D_PROJECT_KEY,
  task_id: 'AI3D-003',
  status: pass ? 'PASS' : 'FAIL',
  verified_fields: [
    'project_key',
    'task_id',
    'run_id',
    'command_id',
    'operation',
    'route',
    'parent_artifact_id',
    'source_artifact_ids',
    'module_id',
    'params_sha256',
  ],
  expected_params_sha256: expectedParamsSha256,
  artifact,
  checkpoint: state.checkpoints.at(-1) ?? null,
  qa: state.qa_reports.at(-1) ?? null,
  final_state: state,
};

const outputPath = path.join(outDir, 'lineage_smoke_result.json');
await fs.writeFile(outputPath, JSON.stringify(result, null, 2));
console.log(JSON.stringify({
  status: result.status,
  artifact_id: artifact?.artifact_id ?? null,
  params_sha256: artifact?.params_sha256 ?? null,
  checkpoint_id: result.checkpoint?.checkpoint_id ?? null,
  verified_fields: result.verified_fields,
  output: outputPath,
}, null, 2));

if (!pass) process.exitCode = 1;
