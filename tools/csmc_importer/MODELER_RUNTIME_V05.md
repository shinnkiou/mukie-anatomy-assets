# MODELER runtime capture v0.5

Status: prepared for Windows real-process validation on the authorized personal-use graduation/research model.

## Goal

Capture only the validated CELSYS runtime `character` BLOB rather than dumping the whole CLIP STUDIO MODELER process.

The real v0.3 capture established a UTF-8 marker at a private writable MODELER heap address with this structure:

`u32(20) -> CLIP_STUDIO_3D_DATA2 -> u32(kind_len) -> character -> 16-byte GUID -> inner version -> logical size -> stored size -> payload`

Expected character GUID for the controlled test asset: `19c1747bf2b84da197b9ead412256c5b`.

## v0.5 validation gate

A candidate is accepted only when all of the following hold:

1. process is scored as the real `CLIPStudioModeler.exe` and Observer/self shells are rejected;
2. the four bytes preceding the UTF-8 marker equal little-endian `20`;
3. marker equals `CLIP_STUDIO_3D_DATA2`;
4. payload kind equals `character`;
5. GUID equals the expected controlled-test GUID;
6. inner version and stored size are within conservative sanity bounds.

The dump range is then exactly `header_bytes + stored_size` beginning four bytes before the marker.

## Progress / failure behavior

Both search and dump stages report `0-100%`, MiB processed, MiB/s and read-failure count. Search and dump each have a 180-second timeout and must emit `COMPLETE` or `PARTIAL` with a reason.

The reader uses `VirtualQueryEx` before each dump segment so it will not blindly cross unreadable/guard/no-access regions.

## Output

Private local capture package may contain:

- `runtime_character_candidates.json`
- `runtime_character_0x....bin`
- `runtime_character_dump.json`
- `capture_manifest.json`
- observer log

The runtime BLOB is purchased-model-derived data and must **not** be committed to this public repository. Public GitHub stores code/specification/synthetic tests only.

Prepared ZIP SHA-256: `677922cf8c4e59c0de2da4641535ebf958d29bcb09a8b054fdb3b9126db7c556`.

## Comparator

`runtime_blob_compare.py` compares a raw Observer runtime BLOB against saved CSMC/CS3C character BLOBs. It supports:

- `character.character`
- `character.catalog_data`
- `catalog_character.catalog_data`
- raw runtime BLOB input

and reports metadata/header deltas, first difference, byte-difference ranges and aligned 8-byte block equality.

Local tests before commit:

- original CSMC vs exact extracted raw BLOB: exact equality PASS;
- one-byte synthetic mutation at offset 1000: detected first difference=1000 and different byte count=1.

## Next experiment

A/B/C comparison when available:

- A: original saved CSMC
- B: controlled modified saved CSMC
- C: v0.5 runtime character BLOB

This determines whether MODELER keeps the saved serialization, a modified serialization, or a distinct runtime representation before proceeding toward Mesh/Index/UV/Bone/Weight/Texture extraction.