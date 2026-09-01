# NEVATIA Villa — Source Analysis / Exterior R1

## Goal
Use a rights-clean modern detached-house mesh as structure/massing input, then redesign its exterior as an ordinary contemporary Japanese villa with a wooden deck and visible everyday residential utilities. This is deliberately **not** a ryokan/traditional-inn design.

## Base asset
- Provider: OpenGameArt
- Asset: `Family House Collection`
- Author: Drummyfish
- License: CC0-1.0 on the asset page
- Source: https://opengameart.org/content/family-house-collection
- Archive: `houses_oga_0.zip`
- Archive SHA-256: `d702ce00fd4ab5bd1e375a44f052b7641b8102a860f9d309bad91165c3c25759`
- Selected mesh: `house5_baked.obj`
- Selected mesh SHA-256: `9ebbe8b355e5c99a295f5f673a7d94ab0dae9ae0308987e5c7e920d472bb7796`
- Connected-component derivative SHA-256: `bf229fab6e1d26137f36880c157256d297acb5273fb830cbf7106b6c8822f507`

The source archive and original OBJ remain immutable. The derivative connected-component OBJ only reorganizes faces beneath 17 named component groups so materials and semantic roles can be assigned without changing the source geometry.

## Measured mesh
- vertices: 388
- faces: 352
- connected components: 17
- bounding min: `[-1.059767, -0.774996, -1.642171]`
- bounding max: `[1.074975, 0.900988, 0.773883]`
- source extents: `2.134742 × 1.675984 × 2.416054`
- vertical axis: Y

house5 was preferred over the other five houses because its compact two-storey massing and porch/balcony-like projections offer the clearest conversion path to a deck-oriented villa while still reading as a normal modern residence.

## Japanese scale conversion
The measured width is mapped to nine 910 mm residential modules:
- target width: 9 × 0.91 = **8.19 m**
- uniform scale: **3.8365291918180273**
- derived envelope: approximately **8.19 m W × 9.269 m D × 6.430 m H**

This is a visual design scale, not a structural/code drawing.

## Exterior R1 inventory
### Main architectural read
- light/medium neutral siding base
- charcoal feature field
- black aluminum-style sash
- large sliding glazing toward the deck
- ordinary dark residential entrance door
- compact entrance canopy
- intercom and mail slot

### Wooden deck
- 6.35 m × 2.18 m
- top elevation 0.43 m
- 14 independent deck boards
- independent subframe/feet
- three low steps
- partial 10-slat privacy screen on one side

### Japanese everyday exterior details
- concrete foundation/plinth
- service-side gravel and stepping pavers
- front/rear rain gutters and east/west downspouts
- two outdoor AC units on concrete feet
- fan grilles
- refrigerant pipe covers
- condensate drain hoses
- electric meter box
- residential gas meter + service pipe proxy
- three vent hoods
- weatherproof exterior outlet
- outdoor faucet
- ground drain grates
- two warm wall lights
- small deck planter

## Intentional exclusions
Do not use the following as shortcuts for “Japanese” identity:
- noren
- shoji facade
- torii
- ryokan signage
- excessive traditional lattice
- decorative kawara-heavy roof language

The target is a contemporary detached house one might encounter in an ordinary Japanese residential area, with the deck and restrained material palette giving it villa character.

## Semantic material split
The 17 connected components are assigned semantic roles without modifying the source OBJ:
- main connected shell → opaque siding + roof-face material split
- opening components → physical-transmission glazing
- door component → dark wood
- balcony/platform components → wood
- residual trim/detail components → dark metal

The main shell further separates roof triangles from walls using triangle height and face-normal tests. The wall surface remains opaque and the transparent material families are deliberately limited.

## Research basis
Project canon:
- `ChatGPT_3D_MultiBuilding_Benchmark_20260829/00_REPORT.md`
- `BAR_NEVATIA_DESIGN_SPEC_20260830.md`
- `CHATGPT_BLENDER_NEXT_CHAT_HANDOFF_20260830`

External factual references used during design:
- Nichiha exterior-wall guidance as the contemporary detached-house siding baseline.
- Tokyo Gas Network placement examples for household gas meters on exterior/near-entry walls.
- OpenGameArt asset page for the CC0 base-house collection and provenance.

## Canonical implementation
Base44 `Creative Ops Lab /ai-3d-model-lab` uses recipe op `nevatia_villa_exterior_preset` and button `NEVATIA 別荘外観`.

The villa implementation is now isolated in one shared pure-Three.js builder:
- Base44 path: `src/lib/3d/nevatiaVillaExteriorR1.js`
- SHA-256: `8024c53d8a3dabf78c3b7e89cb48b806900cce7caaaa42b458e4950acbdd0b86`
- GitHub mirror: `tools/voxel_world/nevatia_villa/nevatiaVillaExteriorR1.js`

Both the AI 3D Model Lab and the standalone QA page use this same builder. This avoids a separate QA-only model drifting from production geometry.

## Completed QA
### Round 1 — Structure
**PASS 26/26**

Includes source/object SHA verification, component count, scale and dimensions, deck-to-wall relationship, deck board/subframe contact, step elevation, outdoor AC placement, gutter/eave placement, required exterior asset families, component-split loading and semantic-role checks.

### Round 2 — Material
**PASS 13/13**

Includes opaque siding, limited transparent material families, non-coplanar front overlays, material/geometry separation, utility materials, distinct wall/glass families, no source-texture dependency and no dynamic entities.

### Round 3 — Appearance proxy
**PASS 14/14**

Includes deck proportion, deck depth, feature-wall dominance, partial privacy screen, three-panel sliding opening, ordinary entry details, Japanese everyday utility layer, two outdoor ACs, rainwater layer, warm residential lighting, absence of ryokan shortcut geometry and restrained wood usage.

## Exact WebGL QA
The exact shared builder was rendered in a real headless Chromium WebGL session at seven fixed views:
1. front three-quarter
2. front
3. east/service side
4. rear three-quarter
5. rear
6. west
7. elevated front

Results:
- status: **PASS**
- HTTP: 200
- exact shared builder: true
- scene meshes: 117
- vertex entries: 5,952
- transparent meshes: 14
- lights: 4
- root: `NEVATIA_VILLA_EXTERIOR_R1`
- WebGL: 2.0
- page errors: 0
- console errors: 0
- browser capture JSON SHA-256: `badb693bd0fbcc98da92cb24fb9f49f80593e3af9bccaf9e2c02338bb50c8b82`

After extracting the shared builder, the seven fixed-view image SHA-256 values were regenerated and matched the previous exact-builder render **byte for byte**. The earlier localhost-only Base44 SDK 404 side effect disappeared after isolating the QA page from `AI3DModelLab.jsx`.

## Production verification
- canonical JSON parse: PASS
- Vite production build: PASS
- source OBJ distribution/readback: PASS
- component-split OBJ distribution/readback: PASS
- shared-builder deterministic QA: PASS
- exact WebGL QA: PASS

## Final status
**NEVATIA Villa Exterior R1 = COMPLETE.**

“Complete” here means the exterior R1 implementation, provenance, immutable-source policy, deterministic QA, production build, exact shared-builder WebGL verification, and canonical save/readback are complete. Interior design and floor-plan development are intentionally outside this R1 scope and should begin as a separate phase rather than silently expanding this completion boundary.
