import * as THREE from 'three';

export const NEVER_TEAR_MARS_DECAL_CELLS = {
  WARNING:0, CAUTION:1, FIRE:2, EXIT:3, AIRLOCK:4, MEDICAL:5, STORAGE:6, COMMAND:7,
  COMMUNICATION:8, HANGAR:9, RUNWAY:10, 'LANDING ZONE':11, EMERGENCY:12,
  'HIGH VOLTAGE':13, OXYGEN:14, PRESSURE:15, 'AUTHORIZED PERSONNEL ONLY':16,
  'SECTOR 01':17, 'SECTOR 02':18, 'SECTOR 03':19
};

const MODULE_RULES = [
  { id:'blast_damage_junction', rx:/BLAST|DAMAGE|COLLAPSE|RUBBLE|DEBRIS|BROKEN_BEAM|ZONE_[ABCD]/i, decals:['EMERGENCY','EXIT','FIRE','CAUTION','SECTOR 03'] },
  { id:'external_utilities_antenna', rx:/EXTERNAL_SERVICE|COOLING_UNIT|SERVICE_MANIFOLD|OXYGEN_TANK|FUEL_TANK|ANTENNA|RADAR/i, decals:['OXYGEN','PRESSURE','HIGH VOLTAGE','AUTHORIZED PERSONNEL ONLY','WARNING'] },
  { id:'landing_external', rx:/LANDING|RUNWAY|APRON|BEACON|LIGHT_TOWER/i, decals:['RUNWAY','LANDING ZONE','CAUTION','WARNING'] },
  { id:'hangar', rx:/HANGAR|CRANE|CATWALK|SCAFFOLD|MAINTENANCE_PIT|FLOOR_RAIL/i, decals:['HANGAR','HIGH VOLTAGE','CAUTION','FIRE','EXIT','SECTOR 01'] },
  { id:'central_corridor', rx:/CENTRAL_CORRIDOR|MAIN_CORRIDOR|CORRIDOR_SPINE/i, decals:['EXIT','EMERGENCY','FIRE','SECTOR 01','SECTOR 02'] },
  { id:'vehicle_maintenance', rx:/VEHICLE|SERVICE_BAY|LIFT_PLATFORM|WASTE_OIL|WASTE_COOLANT/i, decals:['CAUTION','HIGH VOLTAGE','FIRE','SECTOR 01'] },
  { id:'maintenance_corridor', rx:/MAINTENANCE_CORRIDOR|SERVICE_CORRIDOR|UTILITY_CORRIDOR/i, decals:['CAUTION','HIGH VOLTAGE','PRESSURE','EXIT','SECTOR 02'] },
  { id:'logistics', rx:/LOGISTICS|WAREHOUSE|HAZMAT|PALLET|CARGO|STORAGE_ZONE|LOGISTICS_RACK/i, decals:['STORAGE','OXYGEN','CAUTION','AUTHORIZED PERSONNEL ONLY','SECTOR 02'] },
  { id:'command_comms_briefing', rx:/COMMAND|COMMUNICATION|COMMS|BRIEFING|SERVER/i, decals:['COMMAND','COMMUNICATION','EXIT','SECTOR 02'] },
  { id:'medical', rx:/MEDICAL|TREATMENT|STRETCHER|MED_BED|OXYGEN_MED/i, decals:['MEDICAL','OXYGEN','EXIT','SECTOR 03'] },
  { id:'quarters_dining', rx:/QUARTER|BUNK|DINING|LOUNGE|KITCHEN/i, decals:['EXIT','SECTOR 03'] },
  { id:'armory', rx:/ARMORY|WEAPON|AMMO/i, decals:['AUTHORIZED PERSONNEL ONLY','CAUTION','SECTOR 02'] },
  { id:'machinery_power', rx:/MACHINE|GENERATOR|UPS|SWITCHBOARD|PUMP|COOLANT|PROCESSOR|POWER/i, decals:['HIGH VOLTAGE','PRESSURE','CAUTION','FIRE','SECTOR 02'] },
  { id:'underground_utilities', rx:/UNDERGROUND|UTILITY_TUNNEL|RISER|SUMP|DRAIN/i, decals:['HIGH VOLTAGE','PRESSURE','CAUTION','SECTOR 03'] }
];

const MODULE_DEFAULTS = {
  landing_external:{damageZone:'D',materials:['concrete','paintedSteel','bareSteel','rubber']},
  hangar:{damageZone:'D',materials:['paintedSteel','bareSteel','concrete','rubber','glass']},
  central_corridor:{damageZone:'D',materials:['paintedSteel','bareSteel','rubber','glass']},
  blast_damage_junction:{damageZone:'A',materials:['paintedSteel','bareSteel','concrete','rubber']},
  vehicle_maintenance:{damageZone:'D',materials:['concrete','paintedSteel','bareSteel','rubber']},
  maintenance_corridor:{damageZone:'D',materials:['paintedSteel','bareSteel','rubber']},
  logistics:{damageZone:'D',materials:['concrete','paintedSteel','bareSteel','rubber']},
  command_comms_briefing:{damageZone:'D',materials:['paintedSteel','rubber','glass']},
  medical:{damageZone:'D',materials:['paintedSteel','rubber','glass']},
  quarters_dining:{damageZone:'D',materials:['paintedSteel','rubber','glass']},
  armory:{damageZone:'D',materials:['paintedSteel','bareSteel','rubber']},
  machinery_power:{damageZone:'D',materials:['paintedSteel','bareSteel','rubber','concrete']},
  external_utilities_antenna:{damageZone:'D',materials:['paintedSteel','bareSteel','rubber']},
  underground_utilities:{damageZone:'D',materials:['paintedSteel','bareSteel','rubber','concrete']},
  generic:{damageZone:'D',materials:['paintedSteel']}
};

export function resolveNeverTearMarsModule(object) {
  const explicit=object?.userData?.neverTearModule||object?.userData?.moduleId;
  if(explicit&&MODULE_DEFAULTS[explicit]) return explicit;
  const haystack=`${object?.name||''} ${object?.userData?.semanticRole||''} ${object?.userData?.assetKey||''}`;
  return MODULE_RULES.find(rule=>rule.rx.test(haystack))?.id||'generic';
}

export function resolveNeverTearMarsMaterialFamily(object,moduleId) {
  const explicit=object?.userData?.materialFamily;
  if(explicit) return explicit;
  const s=`${object?.name||''} ${object?.userData?.semanticRole||''}`.toUpperCase();
  if(/GLASS|WINDOW|GLAZ/.test(s)) return 'glass';
  if(/CONCRETE|FLOOR|APRON|PAD|CURB|SLAB/.test(s)) return 'concrete';
  if(/RUBBER|TIRE|SEAL|HOSE|PAD/.test(s)) return 'rubber';
  if(/BARE|IRON|RAIL|BEAM|STEEL_EXPOSED|CRANE|RACK/.test(s)) return 'bareSteel';
  return MODULE_DEFAULTS[moduleId]?.materials?.[0]||'paintedSteel';
}

export function createNeverTearMarsMaterialLibrary() {
  const paintedSteel=new THREE.MeshStandardMaterial({color:'#71767a',roughness:.58,metalness:.0});
  const bareSteel=new THREE.MeshStandardMaterial({color:'#555b60',roughness:.47,metalness:1});
  const concrete=new THREE.MeshStandardMaterial({color:'#777a78',roughness:.88,metalness:0});
  const rubber=new THREE.MeshStandardMaterial({color:'#202225',roughness:.78,metalness:0});
  const glass=new THREE.MeshPhysicalMaterial({color:'#9eb6bd',roughness:.14,metalness:0,transmission:.90,ior:1.48,thickness:.02,transparent:true,opacity:.62});
  const library={paintedSteel,bareSteel,concrete,rubber,glass};
  Object.entries(library).forEach(([key,mat])=>{mat.name=`NT_MARS_${key}`;mat.userData={neverTearSurfaceLibrary:'v1',materialFamily:key};});
  return library;
}

function inferDamageZone(object,moduleId) {
  const explicit=String(object?.userData?.damageZone||'').toUpperCase();
  if(['A','B','C','D'].includes(explicit)) return explicit;
  const s=`${object?.name||''} ${object?.userData?.semanticRole||''}`.toUpperCase();
  if(/ZONE_A|BLAST_CORE|CHAR|RUBBLE|COLLAPSED|BROKEN_BEAM/.test(s)) return 'A';
  if(/ZONE_B|STRONG_HEAT|BURN/.test(s)) return 'B';
  if(/ZONE_C|SMOKE|SOOT/.test(s)) return 'C';
  return MODULE_DEFAULTS[moduleId]?.damageZone||'D';
}

function damageTuning(zone) {
  if(zone==='A') return {colorMul:.33,roughnessAdd:.18,damageMasks:['burn_char','soot','paint_loss','ash'],dustWeight:.2};
  if(zone==='B') return {colorMul:.58,roughnessAdd:.14,damageMasks:['soot','heat','bubbled_paint','paint_loss'],dustWeight:.4};
  if(zone==='C') return {colorMul:.82,roughnessAdd:.08,damageMasks:['light_soot','grime','mars_dust'],dustWeight:.7};
  return {colorMul:1,roughnessAdd:.03,damageMasks:['mars_dust','service_wear'],dustWeight:1};
}

function cloneAndTuneMaterial(base,zone) {
  const mat=base.clone(); const t=damageTuning(zone);
  if(mat.color) mat.color.multiplyScalar(t.colorMul);
  mat.roughness=Math.min(1,(mat.roughness??.7)+t.roughnessAdd);
  mat.name=`${base.name}_ZONE_${zone}`;
  mat.userData={...(base.userData||{}),damageZone:zone,damageMasks:t.damageMasks,dustWeight:t.dustWeight};
  return mat;
}

export function applyNeverTearMarsSurface(root,options={}) {
  if(!root?.traverse) return {status:'NO_ROOT',meshes:0,modules:{},materials:{},zones:{},decalCells:[],sharedMaterialVariants:0};
  const lib=options.materialLibrary||createNeverTearMarsMaterialLibrary();
  const decalCellSet=new Set(); const tunedMaterialCache=new Map();
  const stats={status:'PASS',meshes:0,modules:{},materials:{},zones:{},decalCells:[],geometryChanged:false,sharedMaterialVariants:0,materialVariantKeys:[]};
  const getSharedTunedMaterial=(family,zone)=>{const key=`${family}:${zone}`;if(!tunedMaterialCache.has(key)){const base=lib[family]||lib.paintedSteel;tunedMaterialCache.set(key,cloneAndTuneMaterial(base,zone));}return tunedMaterialCache.get(key);};
  root.traverse(object=>{
    if(!object?.isMesh) return;
    const moduleId=resolveNeverTearMarsModule(object); const family=resolveNeverTearMarsMaterialFamily(object,moduleId); const zone=inferDamageZone(object,moduleId); const variantKey=`${family}:${zone}`;
    const existingMaterial=object.material;
    const existingReusable=existingMaterial?.userData?.neverTearSurfaceLibrary==='v1'&&existingMaterial?.userData?.materialFamily===family&&existingMaterial?.userData?.damageZone===zone;
    if(existingReusable){if(!tunedMaterialCache.has(variantKey)) tunedMaterialCache.set(variantKey,existingMaterial);object.material=tunedMaterialCache.get(variantKey);} else object.material=getSharedTunedMaterial(family,zone);
    object.userData={...(object.userData||{}),neverTearSurfaceApplied:'v1',neverTearModule:moduleId,materialFamily:family,damageZone:zone,damageMasks:damageTuning(zone).damageMasks,decalCells:(MODULE_RULES.find(rule=>rule.id===moduleId)?.decals||[]).map(x=>NEVER_TEAR_MARS_DECAL_CELLS[x]).filter(Number.isInteger)};
    object.userData.decalCells.forEach(x=>decalCellSet.add(x)); stats.meshes++; stats.modules[moduleId]=(stats.modules[moduleId]||0)+1; stats.materials[family]=(stats.materials[family]||0)+1; stats.zones[zone]=(stats.zones[zone]||0)+1;
  });
  stats.decalCells=[...decalCellSet].sort((a,b)=>a-b); stats.sharedMaterialVariants=tunedMaterialCache.size; stats.materialVariantKeys=[...tunedMaterialCache.keys()].sort(); if(!stats.meshes) stats.status='NO_MATCHING_MESHES'; return stats;
}

export function inspectNeverTearMarsSurface(root) {
  const decalCellSet=new Set(); const materialSet=new Set();
  const stats={meshes:0,applied:0,missingModule:0,missingMaterialFamily:0,zones:{},decalCells:[],geometryMutation:false,uniqueMaterials:0,materialReuseRatio:0};
  root?.traverse?.(o=>{if(!o?.isMesh)return;stats.meshes++;if(o.material)materialSet.add(o.material);if(o.userData?.neverTearSurfaceApplied==='v1')stats.applied++;if(!o.userData?.neverTearModule)stats.missingModule++;if(!o.userData?.materialFamily)stats.missingMaterialFamily++;const z=o.userData?.damageZone;if(z)stats.zones[z]=(stats.zones[z]||0)+1;(o.userData?.decalCells||[]).forEach(x=>decalCellSet.add(x));});
  stats.decalCells=[...decalCellSet].sort((a,b)=>a-b);stats.uniqueMaterials=materialSet.size;stats.materialReuseRatio=stats.uniqueMaterials?Number((stats.meshes/stats.uniqueMaterials).toFixed(2)):0;stats.status=stats.meshes>0&&stats.applied===stats.meshes&&!stats.missingModule&&!stats.missingMaterialFamily?'PASS':'WARN';return stats;
}
