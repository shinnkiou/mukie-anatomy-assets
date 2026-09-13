import * as THREE from 'three';
import { createCheckpointRecord } from './productionProtocol';

function finiteVector(value, fallback) {
  return Array.isArray(value) && value.length === 3 && value.every(Number.isFinite) ? value : fallback;
}

function disposeObject(object) {
  object?.traverse?.((node) => {
    node.geometry?.dispose?.();
    const materials = Array.isArray(node.material) ? node.material : [node.material];
    materials.filter(Boolean).forEach((material) => material.dispose?.());
  });
}

function materialSnapshot(material) {
  const m = Array.isArray(material) ? material[0] : material;
  if (!m) return null;
  return {
    color: m.color?.getHexString ? `#${m.color.getHexString()}` : null,
    roughness: Number.isFinite(m.roughness) ? m.roughness : null,
    metalness: Number.isFinite(m.metalness) ? m.metalness : null,
    emissive: m.emissive?.getHexString ? `#${m.emissive.getHexString()}` : null,
    emissiveIntensity: Number.isFinite(m.emissiveIntensity) ? m.emissiveIntensity : null,
  };
}

function objectSnapshot(object) {
  return {
    name: object.name,
    kind: object.userData?.ai3dKind || object.geometry?.type || object.type,
    position: object.position.toArray(),
    rotation: [object.rotation.x, object.rotation.y, object.rotation.z],
    scale: object.scale.toArray(),
    material: object.isMesh ? materialSnapshot(object.material) : null,
  };
}

function managedSceneSnapshot(scene) {
  const objects = {};
  scene.traverse((object) => {
    if (!object.userData?.ai3dManaged) return;
    objects[object.name || object.uuid] = objectSnapshot(object);
  });
  return objects;
}

function makeGeometry(params) {
  const kind = params.kind;
  if (kind === 'box') {
    const size = finiteVector(params.size, [1, 1, 1]);
    return new THREE.BoxGeometry(...size);
  }
  if (kind === 'cylinder') {
    return new THREE.CylinderGeometry(
      Number.isFinite(params.radius) ? params.radius : 0.5,
      Number.isFinite(params.radius) ? params.radius : 0.5,
      Number.isFinite(params.depth) ? params.depth : 1,
      Number.isFinite(params.segments) ? Math.max(3, Math.floor(params.segments)) : 24,
    );
  }
  if (kind === 'sphere') {
    return new THREE.SphereGeometry(
      Number.isFinite(params.radius) ? params.radius : 0.5,
      32,
      16,
    );
  }
  if (kind === 'plane') {
    const size = finiteVector(params.size, [1, 1, 0]);
    return new THREE.PlaneGeometry(size[0], size[1]);
  }
  throw new Error(`WEBGL adapter unsupported primitive: ${kind}`);
}

function makeMaterial(params = {}) {
  return new THREE.MeshStandardMaterial({
    color: params.color || '#bbbbbb',
    roughness: Number.isFinite(params.roughness) ? params.roughness : 0.75,
    metalness: Number.isFinite(params.metalness) ? params.metalness : 0.05,
    emissive: params.emissive || '#000000',
    emissiveIntensity: Number.isFinite(params.emissiveIntensity) ? params.emissiveIntensity : 0,
  });
}

async function sha256Bytes(bytes) {
  const digest = await globalThis.crypto.subtle.digest('SHA-256', bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength));
  return [...new Uint8Array(digest)].map((x) => x.toString(16).padStart(2, '0')).join('');
}

function pixelsToDataUrl(pixels, width, height) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  if (!context) throw new Error('2D canvas context unavailable for render evidence');
  const image = context.createImageData(width, height);
  const stride = width * 4;
  for (let y = 0; y < height; y += 1) {
    const sourceStart = (height - 1 - y) * stride;
    image.data.set(pixels.subarray(sourceStart, sourceStart + stride), y * stride);
  }
  context.putImageData(image, 0, 0);
  return canvas.toDataURL('image/png');
}

async function capturePixels(ctx, params) {
  const width = Math.max(64, Math.min(2048, Math.floor(params.width || 960)));
  const height = Math.max(64, Math.min(2048, Math.floor(params.height || 540)));
  const renderTarget = new THREE.WebGLRenderTarget(width, height, {
    minFilter: THREE.LinearFilter,
    magFilter: THREE.LinearFilter,
    format: THREE.RGBAFormat,
    type: THREE.UnsignedByteType,
    depthBuffer: true,
    stencilBuffer: false,
  });
  const pixels = new Uint8Array(width * height * 4);
  const previousTarget = ctx.renderer.getRenderTarget();
  try {
    ctx.renderer.setRenderTarget(renderTarget);
    ctx.renderer.clear(true, true, true);
    ctx.renderer.render(ctx.scene, ctx.camera);
    ctx.renderer.readRenderTargetPixels(renderTarget, 0, 0, width, height, pixels);
  } finally {
    ctx.renderer.setRenderTarget(previousTarget);
    renderTarget.dispose();
  }
  const sha256 = await sha256Bytes(pixels);
  const dataUrl = pixelsToDataUrl(pixels, width, height);
  return { pixels, width, height, sha256, dataUrl };
}

function colorEquals(actual, expected) {
  if (!actual || !expected) return false;
  return actual.toLowerCase() === expected.toLowerCase();
}

function vectorsEqual(actual, expected, tolerance = 1e-6) {
  return Array.isArray(actual)
    && Array.isArray(expected)
    && actual.length === expected.length
    && actual.every((value, index) => Math.abs(value - expected[index]) <= tolerance);
}

export function createWebGLProductionAdapter(ctx, options = {}) {
  if (!ctx?.scene || !ctx?.camera || !ctx?.renderer) throw new Error('WEBGL adapter requires scene, camera and renderer');

  return {
    async run(command, route, state) {
      if (route !== 'WEBGL') return { status: 'FAILED', error: `WEBGL adapter cannot run route: ${route}` };
      const { params } = command;

      if (command.op === 'CREATE_PRIMITIVE') {
        const existing = ctx.scene.getObjectByName(params.name);
        if (existing?.parent) {
          existing.parent.remove(existing);
          disposeObject(existing);
        }
        const mesh = new THREE.Mesh(makeGeometry(params), makeMaterial(params));
        mesh.name = params.name;
        mesh.userData.aiGenerated = true;
        mesh.userData.ai3dManaged = true;
        mesh.userData.ai3dKind = params.kind;
        mesh.position.fromArray(finiteVector(params.position, [0, 0, 0]));
        mesh.rotation.fromArray([...finiteVector(params.rotation, [0, 0, 0]), mesh.rotation.order]);
        mesh.scale.fromArray(finiteVector(params.scale, [1, 1, 1]));
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        ctx.scene.add(mesh);
        return { status: 'PASS', object: objectSnapshot(mesh) };
      }

      if (command.op === 'TRANSFORM_SET') {
        const object = ctx.scene.getObjectByName(params.name);
        if (!object) return { status: 'FAILED', error: `object not found: ${params.name}` };
        if (params.position) object.position.fromArray(params.position);
        if (params.rotation) object.rotation.set(...params.rotation);
        if (params.scale) object.scale.fromArray(params.scale);
        object.updateMatrixWorld(true);
        return { status: 'PASS', object: objectSnapshot(object) };
      }

      if (command.op === 'MATERIAL_SET') {
        const object = ctx.scene.getObjectByName(params.name);
        if (!object?.isMesh) return { status: 'FAILED', error: `mesh not found: ${params.name}` };
        const oldMaterial = object.material;
        object.material = makeMaterial(params);
        const oldMaterials = Array.isArray(oldMaterial) ? oldMaterial : [oldMaterial];
        oldMaterials.filter(Boolean).forEach((material) => material.dispose?.());
        return { status: 'PASS', object: objectSnapshot(object) };
      }

      if (command.op === 'CAMERA_SET') {
        if (params.position) ctx.camera.position.fromArray(params.position);
        if (params.target && ctx.controls) ctx.controls.target.fromArray(params.target);
        ctx.controls?.update?.();
        ctx.camera.updateProjectionMatrix();
        return { status: 'PASS', state_patch: { camera: { position: ctx.camera.position.toArray(), target: ctx.controls?.target?.toArray?.() || null } } };
      }

      if (command.op === 'LIGHT_SET') {
        const existing = ctx.scene.getObjectByName(params.name);
        if (existing?.parent) existing.parent.remove(existing);
        let light;
        if (params.kind === 'directional') light = new THREE.DirectionalLight(params.color || '#ffffff', params.intensity ?? 2);
        else if (params.kind === 'ambient') light = new THREE.AmbientLight(params.color || '#ffffff', params.intensity ?? 1);
        else light = new THREE.PointLight(params.color || '#ffffff', params.intensity ?? 8, params.distance ?? 20, params.decay ?? 2);
        light.name = params.name;
        light.userData.aiGenerated = true;
        light.userData.ai3dManaged = true;
        if (params.position) light.position.fromArray(params.position);
        ctx.scene.add(light);
        return { status: 'PASS', object: objectSnapshot(light) };
      }

      if (command.op === 'RENDER_CAPTURE') {
        const capture = await capturePixels(ctx, params);
        const artifact = {
          artifact_id: `webgl-render-${capture.sha256.slice(0, 16)}`,
          type: 'PIXEL_RENDER_EVIDENCE',
          sha256: capture.sha256,
          route: 'WEBGL',
          width: capture.width,
          height: capture.height,
          physical_render: true,
          created_at: new Date().toISOString(),
        };
        options.onRenderCapture?.({ dataUrl: capture.dataUrl, artifact });
        return { status: 'PASS', artifact };
      }

      if (command.op === 'QA_RUN') {
        const checks = params.checks.map((check) => {
          const object = check.name ? ctx.scene.getObjectByName(check.name) : null;
          if (check.type === 'object_exists') return { ...check, pass: Boolean(object) };
          if (check.type === 'position_equals') return { ...check, pass: Boolean(object) && vectorsEqual(object.position.toArray(), check.value) };
          if (check.type === 'rotation_equals') return { ...check, pass: Boolean(object) && vectorsEqual([object.rotation.x, object.rotation.y, object.rotation.z], check.value) };
          if (check.type === 'material_equals') {
            const material = object?.isMesh ? materialSnapshot(object.material) : null;
            return {
              ...check,
              pass: Boolean(material)
                && colorEquals(material.color, check.color)
                && Math.abs((material.roughness ?? 0) - check.roughness) <= 1e-6
                && Math.abs((material.metalness ?? 0) - check.metalness) <= 1e-6,
            };
          }
          if (check.type === 'render_artifact_exists') {
            return { ...check, pass: state.artifacts.some((artifact) => artifact.type === 'PIXEL_RENDER_EVIDENCE' && artifact.physical_render === true) };
          }
          return { ...check, pass: false, error: 'unknown WEBGL QA check' };
        });
        return {
          status: 'PASS',
          qa: {
            qa_id: `webgl-qa-${Date.now()}`,
            status: checks.every((check) => check.pass) ? 'PASS' : 'FAIL',
            checks,
            created_at: new Date().toISOString(),
          },
        };
      }

      if (command.op === 'CHECKPOINT_SAVE') {
        const snapshotState = {
          ...state,
          objects: managedSceneSnapshot(ctx.scene),
        };
        const checkpoint = await createCheckpointRecord(snapshotState, params.name, {
          scope: 'physical-webgl-canary',
          renderer: 'Three.js WebGLRenderer',
          visual_qa_required_before_promotion: true,
        });
        return { status: 'PASS', checkpoint };
      }

      return { status: 'FAILED', error: `WEBGL adapter handler not implemented yet: ${command.op}` };
    },
  };
}
