import fs from 'node:fs/promises';
import path from 'node:path';
import {
  createAssemblyArtifact,
  createModuleRegistry,
  qaAssembly,
  validateAssemblyPlan,
  validateModuleDependencyGraph,
} from '../src/moduleAssembly.js';
import { sha256Hex } from '../src/productionProtocol.js';

const outDir = path.resolve('artifacts/ai3d_module_assembly');
await fs.mkdir(outDir, { recursive: true });

const modules = [
  {
    module_id: 'NT-MOD-HANGAR-A',
    kind: 'ROOM',
    artifact_id: 'module-artifact-hangar-a',
    source_artifact_ids: ['reference-layout-hangar'],
    dependencies: [],
    bounds: { size_m: [12, 4, 18] },
    sockets: [
      {
        socket_id: 'east-doorway',
        socket_type: 'DOORWAY',
        accepts: ['DOORWAY'],
        transform: { position: [6, 0, 0], rotation: [0, 1.5707963268, 0] },
      },
    ],
    metadata: { role: 'primary_volume' },
  },
  {
    module_id: 'NT-MOD-CORRIDOR-A',
    kind: 'STRUCTURE',
    artifact_id: 'module-artifact-corridor-a',
    source_artifact_ids: ['reference-layout-corridor'],
    dependencies: [],
    bounds: { size_m: [3, 3.2, 10] },
    sockets: [
      {
        socket_id: 'west-doorway',
        socket_type: 'DOORWAY',
        accepts: ['DOORWAY'],
        transform: { position: [-1.5, 0, 0], rotation: [0, -1.5707963268, 0] },
      },
      {
        socket_id: 'east-doorway',
        socket_type: 'DOORWAY',
        accepts: ['DOORWAY'],
        transform: { position: [1.5, 0, 0], rotation: [0, 1.5707963268, 0] },
      },
    ],
    metadata: { role: 'circulation' },
  },
  {
    module_id: 'NT-MOD-MEDICAL-A',
    kind: 'ROOM',
    artifact_id: 'module-artifact-medical-a',
    source_artifact_ids: ['reference-layout-medical'],
    dependencies: ['NT-MOD-CORRIDOR-A'],
    bounds: { size_m: [7, 3.2, 8] },
    sockets: [
      {
        socket_id: 'west-doorway',
        socket_type: 'DOORWAY',
        accepts: ['DOORWAY'],
        transform: { position: [-3.5, 0, 0], rotation: [0, -1.5707963268, 0] },
      },
    ],
    metadata: { role: 'medical_room' },
  },
];

const registry = createModuleRegistry(modules);
const dependencyOrder = validateModuleDependencyGraph(registry);

const assemblyPlan = {
  assembly_id: 'NT-ASM-MARS-TEST-A',
  root_instance_id: 'hangar-01',
  instances: [
    {
      instance_id: 'hangar-01',
      module_id: 'NT-MOD-HANGAR-A',
      transform: { position: [0, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] },
    },
    {
      instance_id: 'corridor-01',
      module_id: 'NT-MOD-CORRIDOR-A',
      parent_instance_id: 'hangar-01',
      parent_socket_id: 'east-doorway',
      local_socket_id: 'west-doorway',
      transform: { position: [7.5, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] },
    },
    {
      instance_id: 'medical-01',
      module_id: 'NT-MOD-MEDICAL-A',
      parent_instance_id: 'corridor-01',
      parent_socket_id: 'east-doorway',
      local_socket_id: 'west-doorway',
      transform: { position: [12.5, 0, 0], rotation: [0, 0, 0], scale: [1, 1, 1] },
    },
  ],
  metadata: {
    purpose: 'AI3D-005 deterministic module/assembly smoke',
    physical_render_required_for_visual_promotion: true,
  },
};

const normalizedAssembly = validateAssemblyPlan(assemblyPlan, registry);
const runId = `AI3D-005-MODULE-${Date.now()}`;
const artifact = await createAssemblyArtifact({
  plan: normalizedAssembly,
  registry,
  task_id: 'AI3D-005',
  run_id: runId,
  parent_artifact_id: 'lineage-render-45df38f352bb0829',
});
const qa = await qaAssembly({ artifact, registry });

let negativeCycleRejected = false;
try {
  const badRegistry = createModuleRegistry([
    { ...modules[0], module_id: 'NT-MOD-CYCLE-A', artifact_id: 'cycle-a', dependencies: ['NT-MOD-CYCLE-B'] },
    { ...modules[1], module_id: 'NT-MOD-CYCLE-B', artifact_id: 'cycle-b', dependencies: ['NT-MOD-CYCLE-A'] },
  ]);
  validateModuleDependencyGraph(badRegistry);
} catch {
  negativeCycleRejected = true;
}

let negativeSocketRejected = false;
try {
  const badModules = structuredClone(modules);
  badModules[2].sockets[0].socket_type = 'UTILITY';
  badModules[2].sockets[0].accepts = ['UTILITY'];
  const badRegistry = createModuleRegistry(badModules);
  validateAssemblyPlan(assemblyPlan, badRegistry);
} catch {
  negativeSocketRejected = true;
}

const result = {
  schema: 'never-tear-ai3d-module-assembly-smoke-v1',
  project_key: artifact.project_key,
  task_id: 'AI3D-005',
  status: qa.status === 'PASS' && negativeCycleRejected && negativeSocketRejected ? 'PASS' : 'FAIL',
  run_id: runId,
  dependency_order: dependencyOrder,
  modules: [...registry.values()],
  assembly: normalizedAssembly,
  artifact,
  qa,
  negative_tests: {
    dependency_cycle_rejected: negativeCycleRejected,
    incompatible_socket_rejected: negativeSocketRejected,
  },
};
result.evidence_sha256 = await sha256Hex(result);

const output = path.join(outDir, 'module_assembly_smoke_result.json');
const pretty = JSON.stringify(result, null, 2);
await fs.writeFile(output, pretty);
await fs.writeFile(path.join(outDir, 'module_assembly_smoke_result.sha256'), `${await sha256Hex(pretty)}  module_assembly_smoke_result.json\n`);

console.log(JSON.stringify({
  status: result.status,
  run_id: result.run_id,
  artifact_id: artifact.artifact_id,
  artifact_sha256: artifact.sha256,
  params_sha256: artifact.params_sha256,
  qa: qa.status,
  dependency_order: dependencyOrder,
  negative_tests: result.negative_tests,
  evidence_sha256: result.evidence_sha256,
  output,
}, null, 2));

if (result.status !== 'PASS') process.exitCode = 1;
