# CSMC F02 Oracle Pending Worksheet Supersession v1 — 2026-09-14

Status: `SUPERSESSION_NOTICE_VERIFIED_NOT_EVIDENCE`

## Why this notice exists

A historical Drive file, `CSMC_F02_MUTATION_ORACLE_30_V1_PENDING.md`
(Drive `1X5q9vtb54g3kEl_xqX2OKHAaPYUpjTsN`), contains an early operational order:

1. M11–M17
2. M01–M10
3. M18–M21
4. M22–M30

That file is a pending worksheet, not an oracle result. Its order predates and conflicts with the later
frozen physical-oracle operator sequence.

## Current authoritative operator order

Use the validated v2 operator packet and the frozen Sentinel-9 order only:

`M01 -> M10 -> M13 -> M14 -> M15 -> M18 -> M22 -> M23 -> M30`

Relevant durable state:

- oracle intake v2: Supabase row 180
- Companion structural preregistration: Supabase row 186
- F02 structural map: Supabase row 190
- current external pointer: Supabase row 197 / V6
- oracle branch head: `5db89bc6f0ca20dcb2646b89202ead6b8b53bde2`

## Supersession rule

The historical pending worksheet is retained for audit/history only.

It must **not** be used as the current operator-order authority.
Do not delete or overwrite it; this notice is an append-only reconciliation.

Future manual observation must use the validated v2 operator packet and frozen Sentinel-9 sequence.

## Proof state unchanged

- physical observations: `0/30`
- oracle: `PENDING_MANUAL_ORACLE`
- `EXPLICIT_SERIALIZER_FIELD_READ = UNRESOLVED`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH = UNRESOLVED`
- `semantic_promotion_count = 0`
- Blender emit: blocked
- runtime dispatch: false

This notice creates no physical observation, no consumer proof edge, no semantic claim, and no new hypothesis family.

## Safety / isolation

No MODELER execution, Save/Save As/Ctrl+S, serialization trigger, Worker/Canary/Control Gate action,
RIO-26 mutation, production/mainline mutation, or raw/private payload publication is performed by this reconciliation.
