# MODELER variant-memory cluster findings — 2026-09-03

## Status
`REAL_MODELER_VARIANT_MARKERS_CLUSTERED_IN_PRIVATE_RW_MEMORY`

Source: valid real-process Observer capture `CAPTURE_20260903_000818.zip`.

The capture has 14 marker hits in 5 memory regions. Every relevant region is:

- Windows memory type `MEM_PRIVATE` (`0x20000`)
- protection `PAGE_READWRITE` (`0x04`)

Therefore these marker copies are runtime-allocated writable memory, not static PE image/resource mappings.

## Region clustering

### `パーツ分け小`
Three UTF-16LE hits in one private RW region.
One captured neighborhood also contains the UTF-16LE ASCII-like fragment:

`de_bodypar`

The context window is truncated, so the full identifier is not yet known.

### `パーツ分け中`
Three UTF-16LE hits in a second private RW region.

### `パーツ分け大` + `筋肉脂肪`
Both names occur three times each inside the **same** private RW allocation region.

Around the `筋肉脂肪` hits, the short v0.3 context windows contain repeated UTF-16LE:

`For_Ue4`

and several ASCII identifier-like fragments such as:

- `rm1_end_bb_1`
- `_nky2_bb_b_1`
- `nd_bb_1`
- `ng1_bb_12bb_1`
- `dex2b`

Another nearby UTF-16LE fragment is `ndpinky`.

These strings are truncated by the old ±context capture window. Their exact full names and semantics are **not yet proven**. Some are nevertheless strongly node/bone-name-like and are more structured than ordinary UI label copies.

## Runtime character-header region

The valid UTF-8 `CLIP_STUDIO_3D_DATA2 / character` hit also resides in a separate `MEM_PRIVATE + PAGE_READWRITE` region.

This supports the v0.5 strategy of treating it as a runtime heap serialization candidate rather than a static executable resource.

A second UTF-16LE `CLIP_STUDIO_3D_DATA2` marker exists in another private RW allocation near strings including `ipulator_tool` and `ComicStoryNombre`; this copy may belong to a general CELSYS runtime string/object structure and should not be confused with the validated UTF-8 character header.

## Interpretation

The repeated body-variant names are not all isolated UI constants. In particular, the co-location of `パーツ分け大` and `筋肉脂肪` with structured identifier-like fragments makes a bounded-neighborhood capture worthwhile.

This does **not** yet prove that the nearby fragments are the actual rig hierarchy or that the variant-name copies directly own model data.

## Recommended next runtime extension

After v0.5 targeted character-blob validation, add a semantic-neighborhood mode that:

1. finds each variant-name hit in the real MODELER PID,
2. records region base/type/protection,
3. captures a bounded neighborhood (e.g. ±64 KiB, not a whole-process dump),
4. extracts null-terminated ASCII and UTF-16LE strings,
5. clusters repeated identifiers across variant states,
6. compares the same neighborhoods before/after exactly one body-variant or bone change.

The resulting string/address map can be cross-referenced with ParamScheme targets such as `NodeName`, `PartsBody`, `PartsMaterial`, `PartsTransform`, and `DessindollBoneInfo`.

## Offline analyzer

`observer_marker_context_probe.py`
SHA-256: `e4f0a37ce6f9fc1f3b8c40d28afbf826a69d1c5340663c5f19b19c4a09b0b235`