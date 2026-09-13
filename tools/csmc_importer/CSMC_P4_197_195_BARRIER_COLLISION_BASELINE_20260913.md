# CSMC P4 +197 -> +195 barrier collision baseline — 2026-09-13

Status: REAL FILE-SIDE STATIC PASS / ZERO MODELER ACTIONS / ZERO RUNTIME JOBS.

Aggregate-only result for the known 3,040-byte clip barrier and 3,024-byte CSMC barrier. No private payload values are included.

- aligned 4-byte units: clip 760 distinct; CSMC 756 distinct
- local shared aligned 4-byte units: 0
- clip barrier units found anywhere at aligned 4-byte positions in CSMC: 3 / 760; uniform-random expectation 3.4023; observed/expected 0.8818
- CSMC barrier units found anywhere at aligned 4-byte positions in clip: 3 / 756; uniform-random expectation 2.4508; observed/expected 1.2241
- entropy: clip 7.93834 bits/byte; CSMC 7.94018 bits/byte
- zlib ratio: clip 1.00362; CSMC 1.00364
- byte-histogram Jensen-Shannon divergence: 0.03240 bits

Interpretation: the few surviving 4-byte occurrences are at ordinary collision scale rather than showing excess literal reuse. Combined with the prior qword-extinction result, this supports a densely reserialized local unit inside a continuing ordered neighborhood. It does not identify field semantics or geometry.

Runtime implication: literal barrier bytes are a poor runtime landmark. Prefer the transition event bracketed by the last preserved +197 neighborhood and first resumed +195 neighborhood, then inspect resulting regular buffers for geometry-bearing structure.

Efficiency: user actions 0; MODELER actions 0; runtime jobs 0; repeated closed experiments 0; Production Worker/STABLE changes 0.
