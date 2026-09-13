# NEVER TEAR AI 3D Production Engine

Project key: `never_tear_ai3d_engine`

This line does **not** continue CSMC analysis. It reuses only general architecture and operations learned from CSMC / UKIE AI BRIDGE / PROJECT RELAY: Cloud → Windows Worker → Blender/GPU, durable queues, checkpoint/next_action, artifact lineage, SHA/readback, Canary → QA → Promote, fail-closed bounded execution, route switching, physical evidence and private/public artifact separation.

Private/purchased CSMC captures, model bytes, binary-analysis targets, credentials and other private reverse-engineering data are excluded.

## Architecture

`AI / ChatGPT → 3D Production Planner → Task Queue → 3D Command API → Route Resolver → WebGL Preview OR Windows Worker → Blender/GPU → QA → Artifact Store → Checkpoint / Next Action`

## Run loop

`READ STATE → PLAN → MODEL → QA → FIX → SAVE → READBACK → NEXT_ACTION`

## MVP command surface

- Primitive
- Transform
- Mesh Edit
- Boolean
- Material
- Texture
- Camera
- Light
- Render
- Import
- Export
- Undo
- QA
- Checkpoint

## First vertical slice

The first success is not only “create a cube.” It must create a box, correct its transform, apply a material, produce render evidence, run automated QA, save a SHA-256 checkpoint, read the state back and expose `next_action`.

Base44 protocol smoke is currently PASS. It validates orchestration, bounded fallback, QA, lineage and checkpointing. Physical WebGL/Blender pixel-render visual QA remains a separate mandatory promotion gate.

## Safety

- allowlisted runner keys only; no arbitrary cloud shell payloads
- stable idempotent command IDs
- maximum three bounded routes per command
- no infinite retry of the same broad method
- large binary artifacts are stored externally; ledgers store refs/hashes
- new command handlers stay CANARY until QA PASS
- simulated evidence never substitutes for physical execution evidence
