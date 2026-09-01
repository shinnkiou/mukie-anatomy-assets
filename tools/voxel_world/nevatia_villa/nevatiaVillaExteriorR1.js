import * as THREE from 'three';
import { OBJLoader } from 'three/addons/loaders/OBJLoader.js';

function makeMaterial(color, roughness = 0.75, metalness = 0.05, extra = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness, metalness, ...extra });
}

function addBox(scene, name, size, position, material, rotation = [0, 0, 0]) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(...size), material);
  mesh.name = name;
  mesh.position.set(...position);
  mesh.rotation.set(...rotation);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  mesh.userData.aiGenerated = true;
  scene.add(mesh);
  return mesh;
}

function addCylinder(scene, name, radius, depth, position, material, rotation = [0, 0, 0], segments = 24) {
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius, depth, segments), material);
  mesh.name = name;
  mesh.position.set(...position);
  mesh.rotation.set(...rotation);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  mesh.userData.aiGenerated = true;
  scene.add(mesh);
  return mesh;
}

export async function buildNevatiaVillaExteriorPreset(scene, label = 'NEVATIA VILLA') {
  const root = new THREE.Group();
  root.name = 'NEVATIA_VILLA_EXTERIOR_R1';
  root.userData.aiGenerated = true;
  root.userData.scope = 'villa-exterior-only';
  root.userData.style = 'contemporary Japanese detached house / villa; explicitly not ryokan or traditional inn';
  root.userData.source = 'OpenGameArt Family House Collection / house5_baked.obj';
  root.userData.sourceUrl = 'https://opengameart.org/content/family-house-collection';
  root.userData.license = 'CC0-1.0';
  root.userData.sourceObjSha256 = '9ebbe8b355e5c99a295f5f673a7d94ab0dae9ae0308987e5c7e920d472bb7796';
  root.userData.componentSplitObjSha256 = 'bf229fab6e1d26137f36880c157256d297acb5273fb830cbf7106b6c8822f507';
  root.userData.sourceZipSha256 = 'd702ce00fd4ab5bd1e375a44f052b7641b8102a860f9d309bad91165c3c25759';
  root.userData.sourceStats = { vertices:388, faces:352, connected_components:17, source_extent:[2.134742,1.675984,2.416054] };
  scene.add(root);

  const response = await fetch('/assets/nevatia_villa/house5_components_r1.obj', { cache:'no-store' });
  if (!response.ok) throw new Error(`NEVATIA villa source OBJ fetch failed: ${response.status}`);
  const sourceText = await response.text();
  const source = new OBJLoader().parse(sourceText);
  source.name = 'NEVATIA_SOURCE_HOUSE5_CC0';
  source.userData.sourceAsset = true;

  const SCALE = 8.19 / 2.134742;
  const SRC_CENTER_X = 0.007604;
  const SRC_MIN_Y = -0.774996;
  const SRC_CENTER_Z = -0.434144;
  source.scale.setScalar(SCALE);
  source.position.set(-SRC_CENTER_X*SCALE, -SRC_MIN_Y*SCALE, -SRC_CENTER_Z*SCALE);

  const siding = makeMaterial('#a5a6a3', .88, 0.01);
  const sourceRoof = makeMaterial('#343739', .82, .05);
  const sourceDoor = makeMaterial('#4d3429', .68, .02);
  const sourceTrim = makeMaterial('#303437', .48, .58);
  const sourceWood = makeMaterial('#765039', .63, .02);
  const sourceGlass = new THREE.MeshPhysicalMaterial({ color:'#78949e', roughness:.18, metalness:0, transmission:.68, ior:1.45, thickness:.02, transparent:true, opacity:.58 });
  const sourceGlassComponents = new Set([1,3,4,5,6,7,8,9,10,13]);
  const sourceWoodComponents = new Set([14,15]);
  source.traverse(o => {
    if (!o.isMesh) return;
    const match = /H5_COMP_(\d+)/.exec(o.name || '');
    const comp = match ? Number(match[1]) : -1;
    if (comp === 0) {
      if (o.geometry.index) o.geometry = o.geometry.toNonIndexed();
      if (!o.geometry.attributes.normal) o.geometry.computeVertexNormals();
      const pos=o.geometry.attributes.position;
      o.geometry.clearGroups();
      const a=new THREE.Vector3(), b=new THREE.Vector3(), c=new THREE.Vector3();
      const ab=new THREE.Vector3(), ac=new THREE.Vector3(), n=new THREE.Vector3();
      for(let i=0;i+2<pos.count;i+=3){
        a.fromBufferAttribute(pos,i); b.fromBufferAttribute(pos,i+1); c.fromBufferAttribute(pos,i+2);
        ab.subVectors(b,a); ac.subVectors(c,a); n.crossVectors(ab,ac).normalize();
        const cy=(a.y+b.y+c.y)/3;
        const isRoof=cy>.34 && Math.abs(n.y)>.28;
        o.geometry.addGroup(i,3,isRoof?1:0);
      }
      o.material=[siding,sourceRoof];
      o.userData.semanticRole='SHELL_WALL_ROOF';
    } else if (sourceGlassComponents.has(comp)) {
      o.material=sourceGlass; o.userData.semanticRole='SOURCE_OPENING_GLAZING';
    } else if (comp === 2) {
      o.material=sourceDoor; o.userData.semanticRole='SOURCE_DOOR';
    } else if (sourceWoodComponents.has(comp)) {
      o.material=sourceWood; o.userData.semanticRole='SOURCE_BALCONY_OR_PLATFORM';
    } else {
      o.material=sourceTrim; o.userData.semanticRole='SOURCE_TRIM_OR_METAL_DETAIL';
    }
    o.castShadow = true;
    o.receiveShadow = true;
    o.userData.sourceGeometry = true;
    o.userData.componentIndex = comp;
  });
  root.add(source);

  const charcoal = makeMaterial('#2d3032', .82, .04);
  const black = makeMaterial('#151719', .46, .58);
  const aluminum = makeMaterial('#22272a', .38, .72);
  const whiteMetal = makeMaterial('#d5d5cf', .70, .28);
  const steel = makeMaterial('#7d8285', .43, .82);
  const concrete = makeMaterial('#777775', .95, 0);
  const gravel = makeMaterial('#716f69', .98, 0);
  const wood = makeMaterial('#765039', .61, .02);
  const woodDark = makeMaterial('#4a3024', .69, .02);
  const glass = new THREE.MeshPhysicalMaterial({ color:'#7f9ca5', roughness:.16, metalness:0, transmission:.74, ior:1.45, thickness:.025, transparent:true, opacity:.60 });
  const warmGlass = new THREE.MeshPhysicalMaterial({ color:'#d6b78a', roughness:.26, metalness:0, transmission:.48, ior:1.45, transparent:true, opacity:.68, emissive:'#8d5a2d', emissiveIntensity:.18 });

  const HOUSE_W = 8.19, HOUSE_D = 2.416054*SCALE, HOUSE_H = 1.675984*SCALE;
  const FRONT_Z = (-1.642171 - SRC_CENTER_Z) * SCALE;
  root.userData.derivedDimensionsM = { width:+HOUSE_W.toFixed(3), depth:+HOUSE_D.toFixed(3), height:+HOUSE_H.toFixed(3), module:0.91 };

  addBox(root,'NV_VILLA_FOUNDATION',[HOUSE_W+.18,.32,HOUSE_D+.18],[0,.16,0],concrete);
  addBox(root,'NV_VILLA_SERVICE_GRAVEL',[1.15,.055,HOUSE_D-.35],[HOUSE_W/2+.54,.028,.12],gravel);
  for(let i=0;i<7;i++) addBox(root,`NV_VILLA_SERVICE_PAVER_${i+1}`,[.48,.035,.48],[HOUSE_W/2+.48,.055,-3.20+i*1.05],concrete);

  addBox(root,'NV_VILLA_FRONT_FEATURE',[4.48,2.72,.055],[.62,1.72,FRONT_Z-.045],charcoal);
  addBox(root,'NV_VILLA_SLIDER_SHADOW',[3.42,2.18,.035],[.88,1.38,FRONT_Z-.085],black);
  for(let i=0;i<3;i++) {
    const x=-.25+i*1.12;
    addBox(root,`NV_VILLA_SLIDER_FRAME_${i+1}`,[1.04,2.10,.055],[x+.03,1.38,FRONT_Z-.13],aluminum);
    addBox(root,`NV_VILLA_SLIDER_GLASS_${i+1}`,[.91,1.94,.022],[x+.03,1.38,FRONT_Z-.165],i===1?warmGlass:glass);
  }
  addBox(root,'NV_VILLA_SLIDER_TOP_RAIL',[3.48,.09,.09],[.88,2.47,FRONT_Z-.15],aluminum);
  addBox(root,'NV_VILLA_SLIDER_BOTTOM_RAIL',[3.48,.075,.09],[.88,.31,FRONT_Z-.15],aluminum);

  addBox(root,'NV_VILLA_ENTRY_RECESS',[1.20,2.28,.045],[-2.62,1.30,FRONT_Z-.10],black);
  addBox(root,'NV_VILLA_ENTRY_DOOR',[.94,2.10,.055],[-2.62,1.28,FRONT_Z-.15],woodDark);
  addBox(root,'NV_VILLA_ENTRY_GLASS',[.20,.82,.024],[-2.84,1.43,FRONT_Z-.19],warmGlass);
  addBox(root,'NV_VILLA_ENTRY_HANDLE',[.045,.42,.055],[-2.25,1.23,FRONT_Z-.22],steel);
  addBox(root,'NV_VILLA_ENTRY_CANOPY',[1.72,.105,.92],[-2.62,2.48,FRONT_Z-.42],charcoal,[.035,0,0]);
  addBox(root,'NV_VILLA_INTERCOM',[.12,.22,.055],[-1.94,1.42,FRONT_Z-.20],black);
  addBox(root,'NV_VILLA_MAIL_SLOT',[.30,.10,.045],[-1.94,1.10,FRONT_Z-.20],aluminum);

  const DECK_W=6.35, DECK_D=2.18, DECK_Y=.43, deckCenterZ=FRONT_Z-DECK_D/2-.04;
  addBox(root,'NV_VILLA_DECK_SUBFRAME',[DECK_W,.18,DECK_D],[.18,DECK_Y-.105,deckCenterZ],black);
  for(let i=0;i<14;i++) {
    const z=deckCenterZ-DECK_D/2+.10+i*((DECK_D-.20)/13);
    addBox(root,`NV_VILLA_DECK_BOARD_${String(i+1).padStart(2,'0')}`,[DECK_W,.045,.125],[.18,DECK_Y,z],wood);
  }
  for(let x of [-2.72,-.8,1.10,3.02]) addBox(root,`NV_VILLA_DECK_FOOT_${x}`,[.20,.34,.28],[x,.17,deckCenterZ],concrete);
  for(let s=0;s<3;s++) addBox(root,`NV_VILLA_DECK_STEP_${s+1}`,[2.05,.14,.34],[.15,.35-s*.12,deckCenterZ-DECK_D/2-.18-s*.27],wood);

  addBox(root,'NV_VILLA_PRIVACY_TOP',[.10,.10,DECK_D-.12],[3.42,2.20,deckCenterZ],woodDark);
  for(let i=0;i<10;i++) {
    const z=deckCenterZ-DECK_D/2+.14+i*((DECK_D-.28)/9);
    addBox(root,`NV_VILLA_PRIVACY_SLAT_${i+1}`,[.075,1.72,.075],[3.42,1.33,z],woodDark);
  }

  const gutterY=Math.min(HOUSE_H-.85,5.35), gutterZ=HOUSE_D/2-.12;
  addCylinder(root,'NV_VILLA_GUTTER_REAR',.052,HOUSE_W-.35,[0,gutterY,gutterZ],charcoal,[0,0,Math.PI/2],20);
  addCylinder(root,'NV_VILLA_GUTTER_FRONT',.052,HOUSE_W-.35,[0,gutterY,-gutterZ],charcoal,[0,0,Math.PI/2],20);
  addCylinder(root,'NV_VILLA_DOWNSPOUT_E',.044,gutterY-.20,[HOUSE_W/2-.20,gutterY/2,-gutterZ],steel,[0,0,0],18);
  addCylinder(root,'NV_VILLA_DOWNSPOUT_W',.044,gutterY-.20,[-HOUSE_W/2+.20,gutterY/2,gutterZ],steel,[0,0,0],18);

  const serviceX=HOUSE_W/2+.30;
  [0.65,2.75].forEach((z,i)=>{
    addBox(root,`NV_VILLA_AC_CASE_${i+1}`,[.46,.68,.86],[serviceX,.53,z],whiteMetal);
    addCylinder(root,`NV_VILLA_AC_FAN_${i+1}`,.245,.028,[serviceX+.245,.55,z],charcoal,[0,0,Math.PI/2],32);
    addCylinder(root,`NV_VILLA_AC_FAN_RING_${i+1}`,.276,.018,[serviceX+.265,.55,z],steel,[0,0,Math.PI/2],32);
    addBox(root,`NV_VILLA_AC_FOOT_A_${i+1}`,[.34,.10,.18],[serviceX-.10,.13,z-.25],concrete);
    addBox(root,`NV_VILLA_AC_FOOT_B_${i+1}`,[.34,.10,.18],[serviceX-.10,.13,z+.25],concrete);
    addBox(root,`NV_VILLA_AC_PIPE_VERT_${i+1}`,[.075,1.62,.095],[HOUSE_W/2+.055,1.65,z+.36],whiteMetal);
    addBox(root,`NV_VILLA_AC_PIPE_HORIZ_${i+1}`,[.31,.075,.095],[HOUSE_W/2+.16,2.44,z+.36],whiteMetal);
    addCylinder(root,`NV_VILLA_AC_DRAIN_${i+1}`,.014,.65,[serviceX-.08,.25,z+.40],whiteMetal,[0,0,0],12);
  });
  addBox(root,'NV_VILLA_ELECTRIC_METER_BOX',[.13,.58,.38],[HOUSE_W/2+.08,1.46,-1.50],whiteMetal);
  addCylinder(root,'NV_VILLA_GAS_METER_BODY',.13,.32,[HOUSE_W/2+.16,1.22,-2.15],steel,[0,0,Math.PI/2],24);
  addCylinder(root,'NV_VILLA_GAS_PIPE_VERT',.025,1.22,[HOUSE_W/2+.08,.61,-2.15],steel,[0,0,0],14);
  addBox(root,'NV_VILLA_EXT_OUTLET',[.09,.14,.11],[HOUSE_W/2+.08,.58,-.85],whiteMetal);
  addCylinder(root,'NV_VILLA_OUTDOOR_FAUCET',.026,.18,[HOUSE_W/2+.09,.70,-.34],steel,[0,0,Math.PI/2],14);
  for(let i=0;i<3;i++) addBox(root,`NV_VILLA_VENT_HOOD_${i+1}`,[.13,.24,.30],[HOUSE_W/2+.09,2.15+i*.58,-3.15],steel,[0,0,-.10]);

  for(let i=0;i<5;i++) addBox(root,`NV_VILLA_DRAIN_GRATE_${i+1}`,[.42,.025,.14],[HOUSE_W/2+.45,.07,-3.15+i*1.35],steel);
  [[-2.62,2.66,FRONT_Z-.34],[2.65,2.60,FRONT_Z-.22]].forEach((p,i)=>{
    addBox(root,`NV_VILLA_WALL_LIGHT_${i+1}`,[.14,.20,.12],p,black);
    const light=new THREE.PointLight('#ffc684',6.2,4.2,2); light.position.set(p[0],p[1]-.06,p[2]-.18); light.userData.aiGenerated=true; light.name=`NV_VILLA_WARM_LIGHT_${i+1}`; root.add(light);
  });

  addBox(root,'NV_VILLA_DECK_PLANTER',[.82,.38,.34],[2.65,.62,deckCenterZ-.52],charcoal);
  for(let i=0;i<5;i++) addCylinder(root,`NV_VILLA_PLANT_${i+1}`,.05,.46,[2.45+i*.10,.97,deckCenterZ-.52],makeMaterial('#52664b',.92,0),[0,0,(i-2)*.12],10);

  root.userData.exteriorDetailInventory = [
    'fiber-cement siding base','charcoal feature wall','black aluminum sash','large sliding deck doors','ordinary entry door/canopy/intercom/mail slot',
    'wood deck/subframe/steps','partial privacy slats','foundation/plinth','service gravel/pavers','gutter/downspouts',
    '2 outdoor AC units','fan grills','refrigerant pipe covers','condensate drains','electric meter','gas meter/piping','vent hoods',
    'exterior outlet','outdoor faucet','drain grates','wall lights','small planter'
  ];
  root.userData.excludedMotifs = ['ryokan signage','noren','shoji facade','torii','decorative kawara emphasis','traditional inn lattice overload'];
  root.userData.qaPlan = ['structure/ground-contact/opening-overlap','material/opacity/double-surface','appearance/scale/repetition/lighting'];
  root.userData.materialPolicy = 'procedural/plain project-owned materials only; source texture pack is not required for derivative';
  root.userData.label = label;
  return root;
}
