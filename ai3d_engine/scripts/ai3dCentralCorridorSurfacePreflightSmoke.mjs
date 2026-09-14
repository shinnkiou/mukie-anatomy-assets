import fs from 'node:fs';
import crypto from 'node:crypto';

const root = new URL('../', import.meta.url);
const readText = (rel) => fs.readFileSync(new URL(rel, root), 'utf8');
const sha256 = (s) => crypto.createHash('sha256').update(s).digest('hex');

const contractText = readText('data/central_corridor_surface_binding_contract_v1.json');
const assignmentText = readText('data/central_corridor_surface_assignment_v1.json');
const inventoryText = readText('data/ai3d010_existing_asset_reuse_inventory.json');
const contract = JSON.parse(contractText);
const assignment = JSON.parse(assignmentText);
const inventory = JSON.parse(inventoryText);

const expectedLegacyAssets = [
  'NT-BLD-025-blast-painted-steel-rust-edge-v1',
  'NT-BLD-025-damaged-emergency-light-lens-v1',
  'NT-BLD-025-blast-floor-dust-ash-v1',
  'NT-BLD-025-ruptured-service-pipe-v1',
  'NT-BLD-025-soot-char-deposit-v1'
];
const expectedImplementationOrder = [
  'applyDoorFrameWearSurface',
  'applyDoorStatusLampSurface',
  'applyWallServicePanelSurface',
  'applyTraySupportSurface',
  'applyCeilingLightSurface',
  'applyOverheadDuctSurface',
  'applyCableTraySurface',
  'applyConduitClipSurface',
  'applyVentGrilleSurface',
  'applyIntercomSurface',
  'applySurvivingFastenerSurface',
  'applyBulkheadFrameSurface'
];
const allowedFamilies = new Set(['paintedSteel','bareSteel','concrete','rubber','emissive','decal','dustOverlay','plastic','glass']);
const ids = contract.bindings.map((b) => b.id);
const functions = new Set(contract.surface_execution_order);
const bindingAssets = new Set(contract.bindings.map((b) => b.surface_asset));
const legacySet = new Set(contract.verified_legacy_localized_surface_assets);
const inventoryLegacy = new Set(inventory.surface_assets_already_present || []);

const checks = {
  schema: contract.schema === 'never-tear-ai3d-central-corridor-surface-binding-v1',
  task: contract.task_id === 'AI3D-012' && contract.module_id === 'MARS_CENTRAL_CORRIDOR',
  evidence_class_not_physical: contract.evidence_class === 'DETERMINISTIC_SURFACE_BINDING_PREFLIGHT_NOT_PHYSICAL',
  authority_revision: contract.structure_authority.authority_revision === 380 && contract.structure_authority.current_revision === 423,
  authority_geometry_sha: contract.structure_authority.geometry_sha256 === '0efa7547c1e065304d93eb5fb0cc858e668c41c3bc6516d0b7ab84302f6f52fb',
  authority_counts: contract.structure_authority.wall_count === 13 && contract.structure_authority.opening_count === 13,
  no_post_authority_geometry_edits: contract.structure_authority.post_authority_wall_or_opening_edits === 0,
  no_structure_mutation: contract.hard_invariants.structure_geometry_mutation === false,
  no_delete: contract.hard_invariants.delete_existing_assets === false,
  reuse_first: contract.hard_invariants.reuse_existing_assets_first === true,
  preserve_pbr: contract.hard_invariants.preserve_existing_pbr === true,
  no_baked_lighting: contract.hard_invariants.no_baked_lighting === true,
  no_uniform_random_damage: contract.hard_invariants.uniform_random_damage === false,
  no_whole_base_blackening: contract.hard_invariants.whole_base_blackening === false,
  no_adobe_geometry_truth: contract.hard_invariants.adobe_geometry_truth_eligible === false,
  no_failed_to3d_geometry_truth: contract.hard_invariants.to3d_failed_job_geometry_truth_eligible === false,
  physical_not_claimed: contract.hard_invariants.physical_execution_claimed === false && contract.hard_invariants.canary_promoted === false,
  binding_count_minimum: contract.bindings.length >= 16,
  binding_ids_unique: new Set(ids).size === ids.length,
  material_families_allowed: contract.bindings.every((b) => allowedFamilies.has(b.material_family)),
  every_binding_has_selector: contract.bindings.every((b) => b.selector && Object.keys(b.selector).length > 0),
  every_binding_has_existing_asset: contract.bindings.every((b) => typeof b.surface_asset === 'string' && b.surface_asset.startsWith('NT-BLD-025-')),
  every_binding_implementation_in_order: contract.bindings.every((b) => functions.has(b.implementation)),
  required_implementation_order_present: expectedImplementationOrder.every((fn) => functions.has(fn)),
  legacy_assets_exact: expectedLegacyAssets.length === legacySet.size && expectedLegacyAssets.every((a) => legacySet.has(a)),
  inventory_legacy_assets_match: expectedLegacyAssets.every((a) => inventoryLegacy.has(a)),
  assignment_preserves_geometry: assignment.policy?.structure_geometry_mutation === false,
  assignment_reuses_assets: assignment.policy?.reuse_existing_assets_first === true,
  assignment_physical_not_claimed: assignment.policy?.physical_execution_claimed === false,
  causal_order_exact: JSON.stringify(contract.blast_damage_causal_order) === JSON.stringify(['blast_pressure','heat','fire','structural_failure','electrical_failure','secondary_fire']),
  promotion_gate_count: contract.promotion_gates.length === 3,
  physical_canary_gate_present: contract.promotion_gates.includes('AI3D-002 physical CANARY PASS'),
  physical_qa_gate_present: contract.promotion_gates.includes('AI3D-004 real Physical QA PASS'),
  structure_module_gate_present: contract.promotion_gates.includes('Central Corridor physical Structure Module QA PASS'),
  adobe_boundary: contract.external_boundaries.adobe_reference_count === 6 && contract.external_boundaries.adobe_role === 'NON_CANONICAL_VISUAL_REFERENCE',
  to3d_boundary: contract.external_boundaries.to3d_status === 'FAILED_OUTPUT_NULL_NO_RETRY',
  walkmyplan_boundary: contract.external_boundaries.walkmyplan_current_revision === 423,
  binding_asset_set_nonempty: bindingAssets.size > 0
};

const failed = Object.entries(checks).filter(([,v]) => !v).map(([k]) => k);
const evidence = {
  schema: 'never-tear-ai3d-surface-preflight-smoke-evidence-v1',
  task_id: 'AI3D-012',
  status: failed.length ? 'FAIL' : 'PASS',
  evidence_class: 'LOGIC_QA_ONLY_NOT_PHYSICAL',
  physical_execution_claimed: false,
  canary_promoted: false,
  contract_sha256: sha256(contractText),
  assignment_sha256: sha256(assignmentText),
  reuse_inventory_sha256: sha256(inventoryText),
  binding_count: contract.bindings.length,
  unique_surface_asset_count: bindingAssets.size,
  legacy_surface_asset_count: legacySet.size,
  checks,
  failed_checks: failed,
  next_action: failed.length
    ? 'Fix only the failed deterministic preflight checks. Do not alter Structure geometry or claim physical execution.'
    : 'Preflight logic is ready. Preserve physical HOLD until AI3D-002, AI3D-004, and Central Corridor physical Structure Module QA all PASS.'
};

const out = new URL('evidence/ai3d012_surface_preflight_evidence.json', root);
fs.mkdirSync(new URL('evidence/', root), { recursive: true });
fs.writeFileSync(out, `${JSON.stringify(evidence, null, 2)}\n`);
console.log(JSON.stringify(evidence, null, 2));
if (failed.length) process.exit(1);
