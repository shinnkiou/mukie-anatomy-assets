# Runtime character BLOB comparator v0.2 — 2026-09-03

## Status
`PAYLOAD_ALIGNED_AND_MOVED_BLOCK_ANCHOR_COMPARATOR_READY`

Observer v0.5 may return a runtime `character` serialization that differs from saved CSMC by an insertion/deletion. A pure same-offset comparison can then make the remainder look unrelated even when it merely shifted.

v0.2 compares relative to the CELSYS `payload_offset` and adds deterministic sampled 8-byte anchors whose positions survive insertion/deletion shifts.

## New outputs
- `stored_minus_align8_logical`
- payload-relative aligned 8-byte equality
- sampled unique 8-byte anchors
- anchor Jaccard overlap
- top position-delta peaks in blocks/bytes

## Synthetic validation
Identity, one-byte mutation, and one 8-byte insertion all PASS.

For the insertion fixture, ordinary positional equality collapses after the insertion but sampled anchors recover:
- +8-byte peak: 87 anchors
- 0-byte pre-insertion peak: 20 anchors
- 107 shared anchors total

On the existing original CSMC identity fixture, the observed relation is:

`stored_size - align_up(logical_size, 8) = 8`

This is recorded as a structural measurement only; it is not asserted to identify a specific cipher or padding scheme.

## Hashes
- runtime_blob_compare.py: `f59ed13a03dc1ade7ed2dc82ceea341ca9a1e706874fe6b52d4c8c4d6305080b`
- test_runtime_blob_compare_synthetic.py: `d6fd18b36d77acc48bbf0e141b2948e12916bc494f32c98aabd9af8aff12732f`

## Commits
- comparator update: `3b5dabaf329c8425af15c6f5e38ecf737a21610d`
- test: `29bff5a3d77746d315e759e507119c4a4e4e8fb4`
- CI update: `0dbf355a5ec21cc6e5a2dab98744bf982d414ef0`

## Next
Use v0.2 immediately on the first real Observer v0.5 runtime dump. If position-aligned equality drops after a local insertion/deletion, use anchor delta peaks before deciding the two serializations are globally different.
