import * as THREE from 'three';

export const NEVER_TEAR_MARS_CANONICAL_PREVIEW_VERSION='2026-09-04-r1';
export const NEVER_TEAR_MARS_PLAN_ID='aacb32598eb746758d60c8';

// Runtime QA proxy derived from durable WalkMyPlan/Drive Structure canon.
// X/Z follow WalkMyPlan X/Y; Three.js Y is vertical. This does not replace WalkMyPlan geometry.
export const NEVER_TEAR_MARS_CANONICAL_PREVIEW_SPEC=[
{name:'LANDING_APRON',module:'landing_external',family:'concrete',zone:'D',task:'NT-BLD-002',size:[24,.22,22],pos:[-22,.11,21],source:'landing pad x[-34,-10] y[10,32]'},
{name:'HANGAR_FLOOR',module:'hangar',family:'concrete',zone:'D',task:'NT-BLD-003',size:[28,.22,22],pos:[14,.11,21],source:'hangar west of corridor x=28; door/pit/rail canon'},
{name:'HANGAR_CRANE_RAIL',module:'hangar',family:'bareSteel',zone:'D',task:'NT-BLD-003',size:[20,.25,.25],pos:[14,3,12],source:'crane rail [4,12]-[24,12]'},
{name:'CENTRAL_CORRIDOR_SPINE',module:'central_corridor',family:'paintedSteel',zone:'D',task:'NT-BLD-006',size:[44,.22,4],pos:[50,.11,20],source:'corridor bbox x[28,72] y[18,22]'},
{name:'ZONE_D_INTACT_BOUNDARY',module:'blast_damage_junction',family:'paintedSteel',zone:'D',task:'NT-BLD-015',size:[17,.05,13],pos:[68,.035,20],source:'Zone D boundary x[59.5,76.5] y[13.5,26.5]'},
{name:'ZONE_C_SMOKE_HEAT',module:'blast_damage_junction',family:'paintedSteel',zone:'C',task:'NT-BLD-015',size:[12.5,.07,9.6],pos:[68.75,.075,20],source:'Zone C x[62.5,75.0] y[15.2,24.8]'},
{name:'ZONE_B_STRONG_HEAT',module:'blast_damage_junction',family:'bareSteel',zone:'B',task:'NT-BLD-015',size:[7.2,.09,6],pos:[69,.125,20],source:'Zone B x[65.4,72.6] y[17.0,23.0]'},
{name:'ZONE_A_RUBBLE',module:'blast_damage_junction',family:'bareSteel',zone:'A',task:'NT-BLD-015',size:[3.6,.8,3.2],pos:[69,.4,20],source:'Zone A x[67.2,70.8] y[18.4,21.6]'},
{name:'VEHICLE_SERVICE_BAY_A',module:'vehicle_maintenance',family:'concrete',zone:'D',task:'NT-BLD-004',size:[4,.3,8],pos:[31,.15,6],source:'service bay A x[29,33] y[2,10]'},
{name:'MAINTENANCE_CORRIDOR_SOUTH',module:'maintenance_corridor',family:'paintedSteel',zone:'D',task:'NT-BLD-007',size:[31,.18,3],pos:[56.3,.09,2.62],source:'room1 center/area current WalkMyPlan readback'},
{name:'LOGISTICS_RACK_WEST',module:'logistics',family:'bareSteel',zone:'D',task:'NT-BLD-005',size:[1,2.5,14],pos:[43.9,1.25,8.75],source:'west rack x[43.4,44.4] y[1,16.5]'},
{name:'BRIEFING_CONSOLE_BLOCK',module:'command_comms_briefing',family:'paintedSteel',zone:'D',task:'NT-BLD-008',size:[4,1.2,2],pos:[30.75,.6,32.98],source:'briefing room center current WalkMyPlan readback'},
{name:'COMMAND_CONSOLE_BLOCK',module:'command_comms_briefing',family:'paintedSteel',zone:'D',task:'NT-BLD-008',size:[4,1.2,1.2],pos:[43,.6,31.95],source:'command room center current WalkMyPlan readback'},
{name:'COMMUNICATION_RACK',module:'command_comms_briefing',family:'bareSteel',zone:'D',task:'NT-BLD-008',size:[4,2.4,1.2],pos:[53,1.2,31.95],source:'comms room center current WalkMyPlan readback'},
{name:'MEDICAL_BED',module:'medical',family:'rubber',zone:'D',task:'NT-BLD-009',size:[2.1,.8,.9],pos:[62,.4,31.95],source:'medical room center current WalkMyPlan readback'},
{name:'QUARTERS_BUNK_BLOCK',module:'quarters_dining',family:'paintedSteel',zone:'D',task:'NT-BLD-010',size:[3,2.4,2],pos:[68.95,1.2,31.95],source:'quarters center current WalkMyPlan readback'},
{name:'DINING_TABLE_BLOCK',module:'quarters_dining',family:'paintedSteel',zone:'D',task:'NT-BLD-010',size:[3,1,2],pos:[68.95,.5,9.05],source:'dining/lounge center current WalkMyPlan readback'},
{name:'ARMORY_RACK',module:'armory',family:'bareSteel',zone:'D',task:'NT-BLD-011',size:[3,2.4,.7],pos:[40.5,1.2,9.05],source:'armory center current WalkMyPlan readback'},
{name:'GENERATOR_A',module:'machinery_power',family:'paintedSteel',zone:'D',task:'NT-BLD-012',size:[4,2.8,2.5],pos:[53,1.4,9.05],source:'machinery room center current WalkMyPlan readback'},
{name:'EMERGENCY_POWER_SWITCHBOARD',module:'machinery_power',family:'paintedSteel',zone:'D',task:'NT-BLD-012',size:[3,2.8,.8],pos:[62,1.4,9.05],source:'emergency power room center current WalkMyPlan readback'},
{name:'EXTERNAL_OXYGEN_TANK_A',module:'external_utilities_antenna',family:'paintedSteel',zone:'D',task:'NT-BLD-013',size:[1.8,3,4],pos:[88.5,1.5,5],source:'fixture77 [88.5,5] 1.8x4.0x3.0m'},
{name:'EXTERNAL_FUEL_TANK_A',module:'external_utilities_antenna',family:'paintedSteel',zone:'D',task:'NT-BLD-013',size:[2.4,3,5],pos:[89,1.5,16.5],source:'fixture79 [89,16.5] 2.4x5.0x3.0m'},
{name:'ANTENNA_MAST_BASE',module:'external_utilities_antenna',family:'bareSteel',zone:'D',task:'NT-BLD-013',size:[2,3,2],pos:[80,1.5,50],source:'fixture81 [80,50] 2.0x2.0x3.0m'},
{name:'UNDERGROUND_UTILITY_TUNNEL',module:'underground_utilities',family:'concrete',zone:'D',task:'NT-BLD-014',size:[54,1.2,3.2],pos:[57,-1.6,20],source:'R46 x[30,84] y[18.4,21.6], projection canon'}
];

function previewMaterial(family){const props={concrete:{color:'#74787a',roughness:.9,metalness:0},paintedSteel:{color:'#73787c',roughness:.6,metalness:.05},bareSteel:{color:'#555b60',roughness:.48,metalness:.9},rubber:{color:'#25272a',roughness:.82,metalness:0},glass:{color:'#91aeb8',roughness:.2,metalness:0}}[family]||{color:'#73787c',roughness:.65,metalness:.05};return new THREE.MeshStandardMaterial(props);}
function addTaggedProxy(root,spec){const mesh=/** @type {any} */(new THREE.Mesh(new THREE.BoxGeometry(...spec.size),/** @type {any} */(previewMaterial(spec.family))));mesh.name=spec.name;mesh.position.set(...spec.pos);mesh.castShadow=true;mesh.receiveShadow=true;mesh.userData={aiGenerated:true,importedModel:true,neverTearCanonicalPreview:true,neverTearModule:spec.module,materialFamily:spec.family,damageZone:spec.zone,semanticRole:spec.name,sourceTask:spec.task,canonicalSource:spec.source,walkmyplanPlanId:NEVER_TEAR_MARS_PLAN_ID,previewVersion:NEVER_TEAR_MARS_CANONICAL_PREVIEW_VERSION};root.add(mesh);return mesh;}
export function buildNeverTearMarsCanonicalPreview(scene){const root=new THREE.Group();root.name='NEVER_TEAR_MARS_CANONICAL_PREVIEW';root.userData={aiGenerated:true,importedModel:true,neverTearCanonicalPreview:true,walkmyplanPlanId:NEVER_TEAR_MARS_PLAN_ID,previewVersion:NEVER_TEAR_MARS_CANONICAL_PREVIEW_VERSION,structureReadback:'50 walls / 26 openings / 87 fixtures',note:'Runtime QA proxy only; does not replace or mutate WalkMyPlan Structure geometry.'};NEVER_TEAR_MARS_CANONICAL_PREVIEW_SPEC.forEach(spec=>addTaggedProxy(root,spec));scene.add(root);return root;}
export function snapshotNeverTearMarsPreviewGeometry(root){const out=[];root?.traverse?.(o=>{if(!o?.isMesh)return;out.push({name:o.name,uuid:o.geometry?.uuid||null,position:o.position.toArray(),rotation:o.rotation.toArray().slice(0,3),scale:o.scale.toArray(),vertexCount:o.geometry?.attributes?.position?.count||0});});return out.sort((a,b)=>a.name.localeCompare(b.name));}
export function compareNeverTearMarsPreviewGeometry(before,after){return{sameMeshCount:before.length===after.length,sameGeometryUuid:JSON.stringify(before.map(x=>[x.name,x.uuid]))===JSON.stringify(after.map(x=>[x.name,x.uuid])),sameTransforms:JSON.stringify(before.map(x=>[x.name,x.position,x.rotation,x.scale]))===JSON.stringify(after.map(x=>[x.name,x.position,x.rotation,x.scale])),sameVertexCounts:JSON.stringify(before.map(x=>[x.name,x.vertexCount]))===JSON.stringify(after.map(x=>[x.name,x.vertexCount]))};}
