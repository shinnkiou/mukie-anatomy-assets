# CSMC ANALYSIS COMPANION C — C-068 public `.clip` source-lineage reconciliation — 2026-09-14

Status: `COMPLETED`

## Why C-068 is admissible

C-067 admitted a genuinely new public `.clip` architecture prior but explicitly warned that repository agreement is not automatically independent replication. After the cross-store current pointer reached Supabase row 194, a new public-safe provenance check was performed against the exact pinned sources used by public-prior v2.

That check found a concrete bookkeeping error in the v2 source role for `wamsoft/clipparse`: the pinned README says the analysis **started from `animeops/clip-tools`**, while also documenting extensive real-file remeasurement, corrections, and real CLIP STUDIO validation. Therefore `INDEPENDENT_REDERIVATION_WITH_MEASURED_NEGATIVE_CONTROL` is too strong as an origin-independence label.

This changes a live confidence hypothesis — source independence — without changing any CSMC semantic claim. It is new evidence rather than a checkpoint restatement, so a numbered run is justified.

## Exact provenance reconciliation

The five pinned public sources remain unchanged:

- `Aodaruma/clipfile-rs` @ `bd88467fa80e63ad48c6c713fbfb5a8a116d798a`
- `youichi-uda/clip-clai` @ `76edfbf393868687107c2cdfdb750a70ca9ba7fe`
- `LavenderSnek/clipdecode` @ `e5347a65202bc399bdd730d13187bc32aabdd4fa`
- `wamsoft/clipparse` @ `322a273c0e059d1dee9132af78289efa12a59522`
- `al3ks1s/clip-tools` @ `e1d3d7ed4701ac84e9220127daa73c2cf90dd803`

The new lineage accounting is deliberately fail-closed:

| Source | Origin-lineage accounting | Empirical revalidation |
|---|---|---|
| `Aodaruma/clipfile-rs` | `UNKNOWN_NOT_COUNTED` | yes — local corpus + minimal-difference validation |
| `youichi-uda/clip-clai` | `KNOWN_DERIVED_NOT_COUNTED` | yes — community sources + CELSYS sample analysis |
| `LavenderSnek/clipdecode` | `UNKNOWN_NOT_COUNTED` | not asserted by this run |
| `wamsoft/clipparse` | `KNOWN_DERIVED_NOT_COUNTED` | yes — starts from `animeops/clip-tools`, then real-file remeasurement and corrections |
| `al3ks1s/clip-tools` | `KNOWN_DERIVED_NOT_COUNTED` | not counted as independent; prior v2 already records upstream parsing/splitting dependencies |

Aggregate bookkeeping:

- pinned repositories: **5**
- guaranteed origin-independent repositories: **0**
- known origin-dependent repositories: **3**
- origin independence unknown / therefore not counted: **2**
- repositories with explicit empirical revalidation in the evidence used here: **3**

`0 guaranteed origin-independent` does **not** mean no author performed independent measurement. It means this Companion lane will not infer a statistically independent vote from repository count when upstream influence is known or unproven.

## What changed from public-prior v2

The following v2 role is downgraded:

`wamsoft/clipparse`:  
`INDEPENDENT_REDERIVATION_WITH_MEASURED_NEGATIVE_CONTROL`  
→ `DEPENDENT_STARTING_POINT_WITH_INDEPENDENT_REAL_FILE_REVALIDATION`

The measured negative control itself is not discarded. Its real-file observations remain useful corroboration. Only the claim that the repository should count as an origin-independent replication is removed.

`youichi-uda/clip-clai` remains correctly described as community analysis plus real-file analysis, but C-068 makes the dependency consequence explicit: it must not increment an independent-replication counter.

`Aodaruma/clipfile-rs` remains the strongest empirical corpus revalidation in the public lane. Its pinned format-analysis explicitly combines local corpus/minimal-difference work with knowledge from public implementations, so C-068 keeps its observations but refuses to infer origin independence from them.

`LavenderSnek/clipdecode` remains useful generic external-indirection corroboration. Its pinned SPEC does not establish enough source-lineage provenance to count it as an independent origin, so it is `UNKNOWN_NOT_COUNTED` rather than promoted or penalized.

## Architecture prior after correction

The structural observation itself survives this audit:

- public `.clip` files can use `ExternalTableAndColumnName` declarations;
- `ExternalChunk.ExternalID -> Offset` supports external-payload indirection;
- public 3D-related schema names remain post-blind corroboration candidates.

Classification stays structurally strong **because of measured corroboration**, not because five repositories are treated as five independent experiments.

New wording:

`STRONG_CORROBORATED_STRUCTURAL_PRIOR_RETAINED / INDEPENDENT_REPLICATION_COUNT_NOT_INFERRED`

## CSMC boundary remains unchanged

C-068 does not transfer `.clip` structure into `.csmc` and does not claim any new MODELER consumer edge.

- `EXPLICIT_SERIALIZER_FIELD_READ`: `UNRESOLVED`
- `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH`: `UNRESOLVED`
- geometry semantics: `UNRESOLVED`
- index topology: `UNRESOLVED`
- F02 physical oracle: `0/30 / PENDING_MANUAL_ORACLE`
- semantic promotion: `0`
- Blender emit: `BLOCKED`

The five frozen blind static questions from the targeted question packet are unchanged. Public names still cannot guide or score the blind pass.

## Machine guard

C-068 adds a validator that rejects:

- counting any of the five repositories as a guaranteed origin-independent vote under the currently documented lineage;
- erasing the `wamsoft/clipparse -> animeops/clip-tools` starting-point dependency;
- erasing the explicit community-source lineage of `clip-clai`;
- turning empirical revalidation into direct CSMC proof;
- changing the physical F02 oracle count without an observation;
- semantic promotion, Blender readiness, runtime dispatch, MODELER execution, Save/serialization, mainline mutation, or RIO-26 mutation.

The guard keeps the useful distinction:

**dependency affects independence accounting; it does not erase independently measured observations.**

## Resume rule

C-069 is not authorized by another restatement of this source graph. A next numbered run still requires one of:

- a new instruction-level direct consumer/static edge satisfying the v2 evidence contract;
- actual validated F02 physical observations;
- real C-051 control/source evidence through C-052 → C-053 → C-054;
- another independent public-safe constraint that materially changes a live hypothesis.

Otherwise switch research axes without incrementing the C-run number.
