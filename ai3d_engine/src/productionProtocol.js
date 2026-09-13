export const AI3D_PROJECT_KEY = 'never_tear_ai3d_engine';

export const AI3D_STAGES = Object.freeze([
  'READ_STATE',
  'PLAN',
  'MODEL',
  'QA',
  'FIX',
  'SAVE',
  'READBACK',
  'NEXT_ACTION',
]);

export const AI3D_OPS = Object.freeze([
  'CREATE_PRIMITIVE',
  'TRANSFORM_SET',
  'MATERIAL_SET',
  'MESH_EDIT',
  'BOOLEAN',
  'TEXTURE_SET',
  'CAMERA_SET',
  'LIGHT_SET',
  'RENDER_CAPTURE',
  'IMPORT_MODEL',
  'EXPORT_MODEL',
  'UNDO',
  'QA_RUN',
  'CHECKPOINT_SAVE',
]);

const TERMINAL_OK = new Set(['PASS', 'SUCCESS']);
const TERMINAL_FAIL = new Set(['FAIL', 'FAILED', 'BLOCKED']);

function isPlainObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

export function stableStringify(value) {
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`;
  if (isPlainObject(value)) {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

export async function sha256Hex(value) {
  const text = typeof value === 'string' ? value : stableStringify(value);
  const bytes = new TextEncoder().encode(text);
  const digest = await globalThis.crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map((x) => x.toString(16).padStart(2, '0')).join('');
}

function assertString(value, name) {
  if (typeof value !== 'string' || !value.trim()) throw new Error(`${name} must be a non-empty string`);
}

function assertVector(value, name, length = 3) {
  if (!Array.isArray(value) || value.length !== length || value.some((v) => !Number.isFinite(v))) {
    throw new Error(`${name} must be a finite ${length}-vector`);
  }
}

export function validateProductionCommand(command) {
  if (!isPlainObject(command)) throw new Error('command must be an object');
  assertString(command.command_id, 'command_id');
  assertString(command.op, 'op');
  if (!AI3D_OPS.includes(command.op)) throw new Error(`unsupported op: ${command.op}`);
  if (!isPlainObject(command.params)) throw new Error('params must be an object');

  const routes = command.routes ?? ['WEBGL'];
  if (!Array.isArray(routes) || routes.length < 1 || routes.length > 3 || routes.some((x) => typeof x !== 'string' || !x)) {
    throw new Error('routes must contain 1-3 non-empty route names');
  }

  if (command.op === 'CREATE_PRIMITIVE') {
    assertString(command.params.name, 'params.name');
    if (!['box', 'cylinder', 'sphere', 'plane'].includes(command.params.kind)) throw new Error('unsupported primitive kind');
    if (command.params.position) assertVector(command.params.position, 'params.position');
    if (command.params.size) assertVector(command.params.size, 'params.size');
  }
  if (command.op === 'TRANSFORM_SET') {
    assertString(command.params.name, 'params.name');
    if (!command.params.position && !command.params.rotation && !command.params.scale) throw new Error('TRANSFORM_SET needs a transform');
    if (command.params.position) assertVector(command.params.position, 'params.position');
    if (command.params.rotation) assertVector(command.params.rotation, 'params.rotation');
    if (command.params.scale) assertVector(command.params.scale, 'params.scale');
  }
  if (command.op === 'MATERIAL_SET') {
    assertString(command.params.name, 'params.name');
    if (command.params.roughness != null && !Number.isFinite(command.params.roughness)) throw new Error('roughness must be finite');
    if (command.params.metalness != null && !Number.isFinite(command.params.metalness)) throw new Error('metalness must be finite');
  }
  if (command.op === 'QA_RUN') {
    if (!Array.isArray(command.params.checks) || command.params.checks.length === 0) throw new Error('QA_RUN needs checks');
  }
  if (command.op === 'CHECKPOINT_SAVE') assertString(command.params.name, 'params.name');

  return { ...command, routes: [...routes], params: { ...command.params } };
}

export function createProductionState(seed = {}) {
  return {
    schema: 'never-tear-ai3d-runtime-v1',
    project_key: AI3D_PROJECT_KEY,
    status: 'READY',
    stage: 'READ_STATE',
    task_id: seed.task_id ?? null,
    run_id: seed.run_id ?? null,
    objects: seed.objects ? structuredClone(seed.objects) : {},
    artifacts: seed.artifacts ? structuredClone(seed.artifacts) : [],
    qa_reports: seed.qa_reports ? structuredClone(seed.qa_reports) : [],
    checkpoints: seed.checkpoints ? structuredClone(seed.checkpoints) : [],
    events: seed.events ? structuredClone(seed.events) : [],
    route_failures: seed.route_failures ? structuredClone(seed.route_failures) : {},
    next_action: seed.next_action ?? null,
    updated_at: new Date().toISOString(),
  };
}

function mergeResultIntoState(state, result) {
  if (result.object) state.objects[result.object.name] = structuredClone(result.object);
  if (result.artifact) state.artifacts.push(structuredClone(result.artifact));
  if (result.qa) state.qa_reports.push(structuredClone(result.qa));
  if (result.checkpoint) state.checkpoints.push(structuredClone(result.checkpoint));
  if (isPlainObject(result.state_patch)) Object.assign(state, structuredClone(result.state_patch));
  state.updated_at = new Date().toISOString();
}

export async function createCheckpointRecord(state, name, metadata = {}) {
  const snapshot = {
    project_key: state.project_key,
    task_id: state.task_id,
    run_id: state.run_id,
    stage: state.stage,
    objects: state.objects,
    artifacts: state.artifacts,
    qa_reports: state.qa_reports,
    metadata,
  };
  const sha256 = await sha256Hex(snapshot);
  return {
    checkpoint_id: `cp-${sha256.slice(0, 16)}`,
    name,
    sha256,
    created_at: new Date().toISOString(),
    snapshot,
  };
}

export async function executeProductionPlan({ plan, adapter, initialState, onEvent }) {
  if (!isPlainObject(plan)) throw new Error('plan must be an object');
  assertString(plan.plan_id, 'plan_id');
  if (!Array.isArray(plan.commands) || plan.commands.length === 0) throw new Error('plan.commands must not be empty');
  if (!adapter || typeof adapter.run !== 'function') throw new Error('adapter.run is required');

  const state = createProductionState({ ...initialState, task_id: plan.task_id ?? initialState?.task_id, run_id: plan.plan_id });
  state.status = 'RUNNING';
  state.stage = 'MODEL';
  const completed = new Set();

  const emit = (event) => {
    const normalized = { at: new Date().toISOString(), ...event };
    state.events.push(normalized);
    onEvent?.(normalized, state);
  };

  for (const rawCommand of plan.commands) {
    const command = validateProductionCommand(rawCommand);
    if (completed.has(command.command_id)) throw new Error(`duplicate command_id in plan: ${command.command_id}`);
    completed.add(command.command_id);

    let success = false;
    let finalError = null;
    for (const route of command.routes) {
      emit({ type: 'COMMAND_ATTEMPT', command_id: command.command_id, op: command.op, route });
      let result;
      try {
        result = await adapter.run(command, route, state);
      } catch (error) {
        result = { status: 'FAILED', error: error?.message || String(error) };
      }

      if (TERMINAL_OK.has(result?.status)) {
        mergeResultIntoState(state, result);
        emit({ type: 'COMMAND_PASS', command_id: command.command_id, op: command.op, route });
        success = true;
        break;
      }

      finalError = result?.error || result?.status || 'unknown failure';
      state.route_failures[route] = (state.route_failures[route] || 0) + 1;
      emit({ type: 'COMMAND_ROUTE_FAIL', command_id: command.command_id, op: command.op, route, error: finalError });
      if (!TERMINAL_FAIL.has(result?.status) && result?.status) finalError = `non-terminal adapter status: ${result.status}`;
    }

    if (!success) {
      state.status = 'BLOCKED';
      state.stage = 'NEXT_ACTION';
      state.next_action = `Switch method or inspect blocker for ${command.command_id}: ${finalError}`;
      emit({ type: 'PLAN_BLOCKED', command_id: command.command_id, error: finalError });
      return state;
    }
  }

  const latestQa = state.qa_reports.at(-1);
  state.status = latestQa && latestQa.status !== 'PASS' ? 'NEEDS_REPAIR' : 'PASS';
  state.stage = state.status === 'PASS' ? 'READBACK' : 'FIX';
  state.next_action = state.status === 'PASS'
    ? 'Read back saved artifacts/checkpoint and promote only after physical/visual evidence when required.'
    : 'Fix failed QA checks and rerun from the latest checkpoint.';
  state.updated_at = new Date().toISOString();
  emit({ type: 'PLAN_FINISHED', status: state.status });
  return state;
}
