# CSMC P4 +197→+195 known +965 grammar exclusion — 2026-09-13

Status: **PUBLIC-SAFE STATIC MAINLINE / ZERO MODELER ACTIONS / ZERO RUNTIME JOBS**

This pass tests a narrow structural hypothesis created by the owner/consumer program:

> Is the +197→+195 open barrier simply an exact concatenation of complete records using the already-known +965 48/49-qword record grammar?

No target bytes are rescanned. The test uses only durable aggregate lengths and the already-verified preservation floor of the +965 record grammar.

## Known +965 grammar

For every complete +965 record:
- length is exactly 48 or 49 qwords;
- q0..20 are always preserved across the two serializations = 21 qwords;
- q25..26 are always preserved = 2 qwords;
- therefore each complete record has at least **23 always-preserved qwords** at fixed corresponding positions.

## +197→+195 open barrier

- clip = 380 qwords
- CSMC = 378 qwords
- complete global aligned-qword extinction across the barrier pair = YES
- transition endpoints themselves are reused anchors outside the open barrier

## Length-composition result

For an exact concatenation of complete +965 records, a region length must be expressible as:

`48*a + 49*b`, where `a,b >= 0`.

The test evaluates both open barriers and conservative variants that include 0, 1, or 2 endpoint qwords.

Clip totals tested: 380, 381, 382 qwords.
CSMC totals tested: 378, 379, 380 qwords.

None has a nonnegative 48/49-record composition.

A stronger simple bound explains why:
- maximum possible length of 7 complete known records = `7*49 = 343` qwords;
- minimum possible length of 8 complete known records = `8*48 = 384` qwords.

Every tested barrier total lies strictly inside the impossible gap **344..383 qwords**.

## Preservation-behavior contradiction

Length alone already rejects exact whole-record concatenation. The correspondence behavior independently disagrees as well:

- one complete +965 record guarantees at least 23 always-preserved qwords;
- the +197→+195 open barrier has complete global aligned-qword extinction.

Therefore the barrier cannot simultaneously be an exact concatenation of complete known +965 records **and** obey the known +965 preservation grammar.

## Classification

`KNOWN_PLUS965_WHOLE_RECORD_CONCATENATION_REJECTED`

## What this does and does not mean

Closed:
- the +197→+195 open barrier is merely 7/8 complete +965 records concatenated together: REJECTED;
- adding one or both reused endpoint qwords repairs that whole-record interpretation: REJECTED;
- the -16 B transition can be explained as simple deletion of the known always-preserved q25..26 16-byte island while otherwise retaining the known +965 correspondence grammar: REJECTED as a literal preserved-island model, because the barrier is globally extinct at aligned qword level.

Still possible:
- +197 and +965 structures share a higher-level owner;
- the barrier contains partial records plus another header/trailer grammar;
- the barrier is a different child serializer grammar inside the same owner;
- unrelated codecs or structures exist inside the barrier.

No semantic owner, codec, geometry, index, UV, material, bone, weight, or Blender-import claim is promoted.

## Consumer impact

This removes one tempting static shortcut from the consumer search. The named consumer should **not** be inferred by simply reusing the known +965 whole-record parser for the +197 barrier.

Current strongest structure remains:

`character external container -> unresolved higher-level ordered owner -> distinct local length-changing child grammar at BND_197_TO_195 -> +195 continuation`

The exact child consumer/function remains the missing edge.
