# NEVATIA Villa — Source Analysis / Exterior R1

Date: 2026-09-01

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

The source archive is never overwritten. The Base44 implementation loads an immutable copy and places derivative exterior assets under a separate `NEVATIA_VILLA_EXTERIOR_R1` root.

## Measured mesh
A lightweight OBJ parser measured the selected house5 mesh:
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
- independent board geometry
- independent subframe/feet
- three low steps
- partial vertical-slat privacy screen on one side

### Japanese everyday exterior details
- concrete foundation/plinth
- service-side gravel and stepping pavers
- front/rear rain gutters and downspouts
- two outdoor AC units on concrete feet
- visible fan grilles
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

## Research basis
Project canon:
- `ChatGPT_3D_MultiBuilding_Benchmark_20260829/00_REPORT.md`
- `BAR_NEVATIA_DESIGN_SPEC_20260830.md`
- `CHATGPT_BLENDER_NEXT_CHAT_HANDOFF_20260830`

External factual references:
- Nichiha exterior-wall Q&A: fiber-cement siding is used on roughly 70% of new detached-house exteriors in Japan.
- Tokyo Gas Network: household gas-meter placement examples include outdoor/near-entry exterior walls.
- OpenGameArt asset page: base house collection is CC0.

## Current implementation state
Base44 `Creative Ops Lab /ai-3d-model-lab` now includes recipe op `nevatia_villa_exterior_preset` and button `NEVATIA 別荘外観`.

Checks completed:
- source OBJ copied into app `public/assets/nevatia_villa/house5_cc0.obj`
- source SHA read back correctly
- Vite production build PASS
- production `dist/assets/nevatia_villa/house5_cc0.obj` SHA matches source
- production JS bundle contains `NEVATIA_VILLA_EXTERIOR_R1`
- canonical JSON parses successfully

Visual QA remains distinct from these machine/readback checks. The project minimum is three QA rounds: structure, material, appearance. Browser/real Blender viewport review must not be falsely marked complete until it is actually observed.
