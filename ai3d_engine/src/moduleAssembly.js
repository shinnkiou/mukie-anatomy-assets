import { AI3D_PROJECT_KEY, sha256Hex, stableStringify } from './productionProtocol.js';

const MODULE_ID_RE = /^[A-Z0-9][A-Z0-9._:-]{2,119}$/;
const INSTANCE_ID_RE = /^[A-Za-z0-9][A-Za-z0-9._:-]{1,119}$/;
const MODULE_KINDS = new Set(['ROOM', 'STRUCTURE', 'EQUIPMENT', 'CHARACTER_PART', 'SURFACE', 'UTILITY']);

function isPlainObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function assertString(value, name) {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${name} must be a non-empty string`);
}

function vec3(value, name, fallback = [0, 0, 0]) {
  if (value == null) return [...fallback];
  if (!Array.isArray(value) || value.length !== 3 || value.some((n) => !Number.isFinite(n))) {
    throw new Error(`${name} must be a finite vec3`);
  }
  return [...value];
}

function uniqueStrings(value, name) {
  if (value == null) return [];
  if (!Array.isArray(value) || value.some((x) => typeof x !== 'string' || !x.trim())) {
    throw new Error(`${name} must be an array of non-empty strings`);
  }
  const result = [...new Set(value.map((x) => x.trim()))];
  if (result.length !== value.length) throw new Error(`${name} must not contain duplicates`);
  return result;
}

export function normalizeTransform(value = {}) {
  if (!isPlainObject(value)) throw new Error('transform must be an object');
  return {
    position: vec3(value.position, 'transform.position', [0, 0, 0]),
    rotation: vec3(value.rotation, 'transform.rotation', [0, 0, 0]),
    scale: vec3(value.scale, 'transform.scale', [1, 1, 1]),
  };
}

export function validateModuleDefinition(raw) {
  if (!isPlainObject(raw)) throw new Error('module must be an object');
  assertString(raw.module_id, 'module_id');
  if (!MODULE_ID_RE.test(raw.module_id)) throw new Error('module_id format rejected');
  if (!MODULE_KINDS.has(raw.kind)) throw new Error(`unsupported module kind: ${raw.kind}`);
  assertString(raw.artifact_id, 'artifact_id');

  const dependencies = uniqueStrings(raw.dependencies, 'dependencies');
  if (dependencies.includes(raw.module_id)) throw new Error('module cannot depend on itself');
  const sourceArtifactIds = uniqueStrings(raw.source_artifact_ids, 'source_artifact_ids');

  if (!Array.isArray(raw.sockets)) throw new Error('sockets must be an array');
  const socketIds = new Set();
  const sockets = raw.sockets.map((socket, index) => {
    if (!isPlainObject(socket)) throw new Error(`socket ${index} must be an object`);
    assertString(socket.socket_id, `sockets[${index}].socket_id`);
    assertString(socket.socket_type, `sockets[${index}].socket_type`);
    if (socketIds.has(socket.socket_id)) throw new Error(`duplicate socket_id: ${socket.socket_id}`);
    socketIds.add(socket.socket_id);
    return {
      socket_id: socket.socket_id,
      socket_type: socket.socket_type,
      accepts: uniqueStrings(socket.accepts, `sockets[${index}].accepts`),
      transform: normalizeTransform(socket.transform),
      metadata: isPlainObject(socket.metadata) ? structuredClone(socket.metadata) : {},
    };
  });

  return {
    schema: 'never-tear-ai3d-module-v1',
    module_id: raw.module_id,
    kind: raw.kind,
    artifact_id: raw.artifact_id,
    source_artifact_ids: sourceArtifactIds,
    dependencies,
    bounds: isPlainObject(raw.bounds) ? structuredClone(raw.bounds) : {},
    sockets,
    metadata: isPlainObject(raw.metadata) ? structuredClone(raw.metadata) : {},
  };
}

export function createModuleRegistry(modules) {
  if (!Array.isArray(modules) || modules.length === 0) throw new Error('modules must not be empty');
  const registry = new Map();
  for (const raw of modules) {
    const module = validateModuleDefinition(raw);
    if (registry.has(module.module_id)) throw new Error(`duplicate module_id: ${module.module_id}`);
    registry.set(module.module_id, module);
  }
  return registry;
}

export function validateModuleDependencyGraph(registry) {
  if (!(registry instanceof Map) || registry.size === 0) throw new Error('module registry required');
  for (const module of registry.values()) {
    for (const dependency of module.dependencies) {
      if (!registry.has(dependency)) throw new Error(`missing dependency ${dependency} for ${module.module_id}`);
    }
  }

  const visiting = new Set();
  const visited = new Set();
  const order = [];
  function visit(moduleId) {
    if (visited.has(moduleId)) return;
    if (visiting.has(moduleId)) throw new Error(`dependency cycle at ${moduleId}`);
    visiting.add(moduleId);
    for (const dep of registry.get(moduleId).dependencies) visit(dep);
    visiting.delete(moduleId);
    visited.add(moduleId);
    order.push(moduleId);
  }
  for (const moduleId of registry.keys()) visit(moduleId);
  return order;
}

function getSocket(module, socketId, name) {
  const socket = module.sockets.find((x) => x.socket_id === socketId);
  if (!socket) throw new Error(`${name} socket not found: ${socketId}`);
  return socket;
}

function socketsCompatible(parentSocket, childSocket) {
  return parentSocket.accepts.includes(childSocket.socket_type)
    && childSocket.accepts.includes(parentSocket.socket_type);
}

export function validateAssemblyPlan(rawPlan, registry) {
  if (!isPlainObject(rawPlan)) throw new Error('assembly plan must be an object');
  assertString(rawPlan.assembly_id, 'assembly_id');
  assertString(rawPlan.root_instance_id, 'root_instance_id');
  if (!Array.isArray(rawPlan.instances) || rawPlan.instances.length === 0) throw new Error('assembly instances required');
  validateModuleDependencyGraph(registry);

  const instances = new Map();
  for (const raw of rawPlan.instances) {
    if (!isPlainObject(raw)) throw new Error('assembly instance must be an object');
    assertString(raw.instance_id, 'instance_id');
    if (!INSTANCE_ID_RE.test(raw.instance_id)) throw new Error('instance_id format rejected');
    assertString(raw.module_id, 'instance.module_id');
    if (!registry.has(raw.module_id)) throw new Error(`unknown module: ${raw.module_id}`);
    if (instances.has(raw.instance_id)) throw new Error(`duplicate instance_id: ${raw.instance_id}`);
    const instance = {
      instance_id: raw.instance_id,
      module_id: raw.module_id,
      parent_instance_id: raw.parent_instance_id ?? null,
      parent_socket_id: raw.parent_socket_id ?? null,
      local_socket_id: raw.local_socket_id ?? null,
      transform: normalizeTransform(raw.transform),
      metadata: isPlainObject(raw.metadata) ? structuredClone(raw.metadata) : {},
    };
    instances.set(instance.instance_id, instance);
  }

  const root = instances.get(rawPlan.root_instance_id);
  if (!root) throw new Error('root_instance_id not found');
  if (root.parent_instance_id || root.parent_socket_id || root.local_socket_id) throw new Error('root instance must not have a parent/socket attachment');

  for (const instance of instances.values()) {
    if (instance.instance_id === root.instance_id) continue;
    if (!instance.parent_instance_id || !instance.parent_socket_id || !instance.local_socket_id) {
      throw new Error(`non-root instance ${instance.instance_id} requires parent and socket ids`);
    }
    const parent = instances.get(instance.parent_instance_id);
    if (!parent) throw new Error(`missing parent instance: ${instance.parent_instance_id}`);
    if (parent.instance_id === instance.instance_id) throw new Error('instance cannot parent itself');
    const parentModule = registry.get(parent.module_id);
    const childModule = registry.get(instance.module_id);
    const parentSocket = getSocket(parentModule, instance.parent_socket_id, 'parent');
    const childSocket = getSocket(childModule, instance.local_socket_id, 'child');
    if (!socketsCompatible(parentSocket, childSocket)) {
      throw new Error(`socket mismatch ${parentSocket.socket_type} ↔ ${childSocket.socket_type}`);
    }
  }

  const visiting = new Set();
  const visited = new Set();
  function visitInstance(instanceId) {
    if (visited.has(instanceId)) return;
    if (visiting.has(instanceId)) throw new Error(`assembly cycle at ${instanceId}`);
    visiting.add(instanceId);
    const parentId = instances.get(instanceId).parent_instance_id;
    if (parentId) visitInstance(parentId);
    visiting.delete(instanceId);
    visited.add(instanceId);
  }
  for (const instanceId of instances.keys()) visitInstance(instanceId);

  const presentModuleIds = new Set([...instances.values()].map((x) => x.module_id));
  for (const instance of instances.values()) {
    const module = registry.get(instance.module_id);
    for (const dependency of module.dependencies) {
      if (!presentModuleIds.has(dependency)) {
        throw new Error(`assembly missing module dependency ${dependency} required by ${module.module_id}`);
      }
    }
  }

  return {
    schema: 'never-tear-ai3d-assembly-v1',
    assembly_id: rawPlan.assembly_id,
    root_instance_id: rawPlan.root_instance_id,
    instances: [...instances.values()],
    metadata: isPlainObject(rawPlan.metadata) ? structuredClone(rawPlan.metadata) : {},
  };
}

export async function createAssemblyArtifact({ plan, registry, task_id = 'AI3D-005', run_id, command_id = 'AI3D-005-ASSEMBLE', parent_artifact_id = null }) {
  const normalizedPlan = validateAssemblyPlan(plan, registry);
  const dependencyOrder = validateModuleDependencyGraph(registry);
  const sourceArtifactIds = [...new Set(normalizedPlan.instances.map((instance) => registry.get(instance.module_id).artifact_id))];
  const paramsSha256 = await sha256Hex({ assembly: normalizedPlan, dependency_order: dependencyOrder });
  const contentSha256 = await sha256Hex({ modules: [...registry.values()], assembly: normalizedPlan, dependency_order: dependencyOrder });
  return {
    artifact_id: `assembly-${contentSha256.slice(0, 16)}`,
    type: 'ASSEMBLY_MODEL',
    sha256: contentSha256,
    project_key: AI3D_PROJECT_KEY,
    task_id,
    run_id,
    command_id,
    operation: 'ASSEMBLY_BUILD',
    route: 'MODULE_ASSEMBLY',
    parent_artifact_id,
    source_artifact_ids: sourceArtifactIds,
    module_id: normalizedPlan.assembly_id,
    params_sha256: paramsSha256,
    dependency_order: dependencyOrder,
    assembly: normalizedPlan,
    created_at: new Date().toISOString(),
  };
}

export async function qaAssembly({ artifact, registry }) {
  const checks = [];
  checks.push({ name: 'artifact_schema', pass: artifact?.type === 'ASSEMBLY_MODEL' && artifact?.operation === 'ASSEMBLY_BUILD' });
  checks.push({ name: 'lineage', pass: artifact?.project_key === AI3D_PROJECT_KEY && typeof artifact?.params_sha256 === 'string' && artifact.params_sha256.length === 64 && Array.isArray(artifact?.source_artifact_ids) && artifact.source_artifact_ids.length > 0 });
  checks.push({ name: 'dependency_graph', pass: (() => { try { validateModuleDependencyGraph(registry); return true; } catch { return false; } })() });
  checks.push({ name: 'assembly_plan', pass: (() => { try { validateAssemblyPlan(artifact.assembly, registry); return true; } catch { return false; } })() });
  const expectedSha = await sha256Hex({ modules: [...registry.values()], assembly: artifact.assembly, dependency_order: artifact.dependency_order });
  checks.push({ name: 'artifact_sha_readback', pass: expectedSha === artifact.sha256 });
  return {
    schema: 'never-tear-ai3d-assembly-qa-v1',
    status: checks.every((x) => x.pass) ? 'PASS' : 'FAIL',
    checks,
    canonical_sha256: expectedSha,
    canonical_json: stableStringify(artifact.assembly),
  };
}
