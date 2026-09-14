# CSMC C-069 2026-09-15 Additional Evidence Reconciliation V1

Classification: `SUPPLEMENTAL_STRUCTURAL_EVIDENCE_RUN_ID_COLLISION`

Supabase row209 and row220 both use logical run name `C-069` but have different sealed hashes. Preserve both provenance chains and do not count them as two numbered runs.

## Additional row220 facts

- C03 `CONTAINER_16B_FIELD_READ_CONFIRMED`: at `0x140d15a90`, `0x1408c0d40` ensures `param_1+0x1e` is 16 bytes and `0x1408c27c0` transfers exactly 16 bytes into it. Scope is `CSFCHUNK_CONTAINER_FIELD`; meaning remains unresolved.
- C04 `CHNKSQLI_LENGTH_BOUNDED_STREAM_COPY_CONFIRMED`: after CHNKSQLi validation, decoded u64 byte length drives remaining -> min(remaining,capacity) -> exact transfer -> remaining decrement. Scope is `CHNKSQLI_CONTAINER_TRANSFER`.

Neither C03 nor C04 proves ExternalID, UUID, checksum, ModelData field width/endian/count, geometry/index/UV/material/bone/weight, or internal model construction.

Companion DQ-02 aligns with mainline `DQ-BRIDGE-LOADER-SER-01`; DQ-03 aligns only after bridge admission with `DQ-SER-WIDTH-01`. No answer is imported from alignment alone.

Current gates remain `STRUCTURAL_ONLY`; `EXPLICIT_SERIALIZER_FIELD_READ=UNRESOLVED`; `CONTROLLED_FIXTURE_TO_CONSUMER_MATCH=UNRESOLVED`; semantic promotion=0; Blender emit=BLOCKED; runtime=false; F02 physical oracle=0/30.
