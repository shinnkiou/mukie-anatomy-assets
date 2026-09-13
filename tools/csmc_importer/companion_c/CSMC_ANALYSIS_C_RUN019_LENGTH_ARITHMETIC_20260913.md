# Companion C — Run C-019

QUESTION: Can known qword lengths reduce numeric codec candidates before any additional data read?

RESULT: Yes. A region of k qwords has length 8k bytes. With a 4-byte count prefix, a 32-bit element array has size 4+4n and a 64-bit element array has size 4+8n. Therefore a whole qword-bounded region cannot have the latter form, while the former requires exactly n=2k-1.

Known cases: 7 qwords -> 13 elements; 20 -> 39; 21 -> 41; 48 -> 95; 49 -> 97.

NEW INFORMATION
- Whole qword-bounded regions need only the 32-bit counted form tested.
- The expected count is fixed and always odd.

CLOSED HYPOTHESES
- Both 32-bit and 64-bit counted forms must be tested on a whole qword-bounded region: rejected.
- Count must be searched over multiple values: rejected.

CONFIDENCE CHANGES
- Length-arithmetic guardrail: VERY HIGH.
- Current codec binding: unchanged and unresolved.

NEXT QUESTION
Can the fixed role partition plus this arithmetic produce an explicit familywise false-positive budget?
