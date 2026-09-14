# CSMC ANALYSIS COMPANION C — RUN C-052
## C-051 BLENDER TEACHER-MANIFEST VALIDATION CONTRACT

## QUESTION

C-051でpreregisterしたsame-identity controlsについて、`.csmc` evidence到着前に、Blender source fixtureそのものが意図した差分を正しく実現していることをpublic-safe metadataだけで検証できるか。

## HYPOTHESIS

source fixtureの設計ミスをCSMC serializer差分として誤読しないためには、Blender側teacher manifestをCSMC解析とは独立してfail-closed検証する必要がある。

## IMPLEMENTATION

追加:
- `csmc_analysis_c_c051_teacher_manifest_validator_c052.py`
- `csmc_analysis_c_c051_blender_teacher_probe_c052.py`
- `test_csmc_analysis_c_c051_teacher_manifest_validator_c052.py`
- `CSMC_ANALYSIS_C_C051_TEACHER_MANIFEST_CONTRACT_C052_20260914.json`

Blender probeは `~/Desktop/CSMC_C051_NEXT_CONTROLS` のC-051 `.blend` sourceだけを開き、次のmetadataをJSON化する。

- mesh object / mesh data names
- mesh object count
- vertices / triangles
- material slot names/count
- actually used material-index cardinality
- UV layer count
- armature / bone names/count
- vertex-group names
- weight-assignment count
- rounded weight histogram

`.csmc`は一切read/writeしない。

## SYNTHETIC TEST

Validator self-test: **12/12 PASS**.

Fail-closed coverage:
- raw CSMC field reject
- material usage 3-vs-1 failure reject
- 3-cube object count failure reject
- UV 0-vs-1 failure reject
- weight assignment cardinality !=16 reject
- unchanged weight histogram reject
- incomplete fixture set reject
- invalid negative count reject
- material identity mismatch reject
- UV identity mismatch reject
- semantic promotion stays zero
- runtime dispatch stays false

## PUBLIC-SAFE RESULT

Validator state: `VALIDATOR_READY_TEACHER_MANIFEST_NOT_YET_ACQUIRED`.

C-051 source `.blend` files themselvesはこのlaneで生成・取得していないため、actual teacher manifestについてPASSを捏造しない。現時点で証明したのは**検証契約とprobeがready**であること。

## NEW INFORMATION

C-051のevidence pipelineを二段階へ分離した。

1. **Blender source realization gate** — C-052 teacher manifest validator
2. **CSMC aggregate gate** — C-051 next-control contract

これにより、例えばMAT3_ALLUSEDで実際にはmaterial index 2が使われていない、UV_OFFにUVが残っている、W25_75でassignment数が変わっている、といったsource-side failureをserialization semanticsへ誤帰属することを防げる。

## NEGATIVE CONTROLS

- source filenameの一致だけでsame identityとしない。
- object/mesh/bone/group/material名とtopology/cardinalityを比較する。
- Blender teacher manifestのPASSはCSMC semantic evidenceではない。
- weight histogram差はweight codecの型やoffsetを確定しない。
- C-052は`.csmc` acquisition authorizationではない。

## REJECTED INTERPRETATIONS

- preregistered Blender scriptが存在すればfixture realizationは自動的に正しい
- CSMC差分を見てからsource-side control failureを判断すれば十分
- teacher-manifest PASSだけでI3 semantic promotionできる
- same filenameならsame identity controlである

## MAINLINE-USEFUL RESULT

Reference-onlyで使用可能:
- source-fixture QA contract
- public-safe teacher manifest schema
- independent Blender metadata probe
- fail-closed same-identity validation rules

使用不可:
- semantic promotion
- Blender content emit
- MODELER/runtime/Worker/Canary/Control Gate dispatch
- RIO-26/mainline mutation

## CONFIDENCE

- C-051 source-QA contract readiness: VERY HIGH
- actual C-051 source realization: NOT YET OBSERVED
- actual C-051 CSMC differential: NOT ACQUIRED
- current render-part candidate: unchanged Level 4 / NOT CONFIRMED

## NEXT QUESTION

C-051 `.blend` sourceが実際に生成された時は、まずC-052 probe + validatorを通す。PASSしたsourceだけを外部のauthorized CSMC conversionへ渡し、得られたaggregateだけをC-051 contractで評価する。

それまでは既存C-050 corpusの同一問いを再実行しない。
