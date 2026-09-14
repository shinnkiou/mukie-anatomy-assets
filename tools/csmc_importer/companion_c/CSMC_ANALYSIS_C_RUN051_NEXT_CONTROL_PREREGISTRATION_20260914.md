# CSMC ANALYSIS COMPANION C — RUN C-051
## NEXT-CONTROL PREREGISTRATION / SAME-IDENTITY FIXTURE DESIGN

## QUESTION

C-050 / mainline reconciliationで得られた Level-4 `TAIL_2456_RENDER_PART_CARDINALITY_CANDIDATE` と、UV / weight の既存confoundを、MODELER/runtimeに触れず次のcontrolled evidenceへ進めるために、最小の追加fixtureをどう設計すべきか。

## HYPOTHESIS

C-050の次に必要なのは既存13 fixtureの再解析ではなく、**competing hypothesesを分離する同一identity control**である。

- material: cadenceが「定義済みmaterial slot数」に従うのか、実際にpolygonから参照されるused partition数に従うのかを分ける。
- object: 1/2 objectの外挿を3 objectsで独立検証する。
- UV: primitive cube既定UVのconfoundを除去し、明示UV OFF/ONを作る。
- weight: assignment cardinality 16を固定し、weight値だけを `0.5/0.5 -> 0.25/0.75` へ変更する。

## REFERENCE-ONLY INPUT

Mainline C-050 reconciliationを一度だけ確認した。

- C-050 outer framing / 2456-byte cadenceはreference-only受理済み。
- mainlineはrender-part-cardinalityを Level 4 candidateとして扱う。
- Level 5 / CONFIRMEDには owner/consumer binding と stricter same-identity controls が不足。
- semantic promotion = 0 / Blender emit BLOCKED / runtime false。

このrunはmainlineの同じpair analysisを再実行しない。

## PREREGISTERED FIXTURES

### Material discriminator

`CSMC_C051_MAT3_ALLUSED`
- 1 mesh object
- 3 material slots
- 3 used material partitions
- predicted cadence = 5

`CSMC_C051_MAT3_ONEUSED`
- 同じ内部object / mesh / material names
- 3 material slotsは保持
- polygon assignmentはslot 0だけ
- discriminator:
  - cadence=5 -> `DEFINED_SLOT_OR_SERIALIZED_PART_COUNT_SUPPORTED`
  - cadence=3 -> `USED_PARTITION_COUNT_SUPPORTED`
  - その他 -> current material cardinality model unresolved

### Object-count validation

`CSMC_C051_THREE_CUBES`
- 3 mesh objects
- explicit materialなし
- predicted cadence = 5 under `2 + render_part` hypothesis

### Clean UV pair

`CSMC_C051_UV_OFF`
- primitive cube作成後、UV layerを明示的に全削除

`CSMC_C051_UV_ON`
- 同じ内部object/mesh identity
- UVを全削除してからSmart Projectで1 layerを明示作成

両方 cadence=3 を予測。ここで初めてUV absent/presentをfixture設計上明示する。

### Weight-scalar pair

`CSMC_C051_W50_50`
`CSMC_C051_W25_75`

両方:
- same mesh topology
- same 2 bones
- same vertex groups
- same 16 assignments
- same internal object/mesh/armature/bone/group names

変更するのは weight値だけ。これでR04→R05に残った「assignment数も変わる」confoundを除去する。

## IMPLEMENTATION

Public-safe only:
- `csmc_analysis_c_next_control_contract_c051.py`
- `csmc_analysis_c_next_control_blender_sources_c051.py`
- manifest JSON
- tests

Blender source generatorは `.blend/.fbx` を作るだけであり、`.csmc`生成、MODELER起動、Save trigger、runtime/Worker/Canary/Control Gateには一切触れない。

## SYNTHETIC TEST

Contract self-test: **11/11 PASS**.

Fail-closed checks:
- unknown fixture reject
- outer framing rule mismatch reject
- unexpected/raw field reject
- incomplete fixture set reject
- material competing-hypothesis branches are explicit
- object cadence mismatch is a refutation, not auto-reinterpretation
- semantic promotion=false
- Blender emit=false
- runtime dispatch=false

## NEW INFORMATION

C-050の「次に何を作るか」を、単なる3-material / 3-object追加から一段厳しくし、**same-identity / competing-hypothesis fixture set**として固定した。

特に `MAT3_ONEUSED` が重要。これにより現在の `render_part` が material slot definition数なのか、used partition数なのかを分けられる。

また、UVとweightについてはC-050で明示した2つのfixture-design weaknessを直接修正する。

## PAIRWISE EVIDENCE STATUS

現時点では **PREREGISTERED_NOT_ACQUIRED**。新しい `.csmc` bytesはまだ存在しない／このlaneでは取得しないため、観測値は捏造しない。

## NEGATIVE CONTROLS

- source fixture generatorの存在を evidence と数えない。
- predicted cadenceを観測結果として扱わない。
- same internal identityでもfile-level metadata confoundが完全消失したとは仮定しない。
- MAT3_ONEUSEDでcadence=5でも「material slot field CONFIRMED」にはしない。
- weight pairで同一lengthでもweight encoding不存在とは言わない。
- weight pairで差分が出ても直接f32/f64とは決めない。

## SEMANTIC CANDIDATES

変更なし。現在:
- render-part cardinality: Level 4 / HIGH candidate, NOT CONFIRMED
- concrete material binding: UNCONFIRMED
- UV binding: UNCONFIRMED
- weight scalar binding: UNCONFIRMED

## REJECTED INTERPRETATIONS

- C-050をもう一度解析すればLevel 5になる
- 3 material slotsだけ追加すればslot-countとused-partitionを区別できる
- R05との比較だけでweight値単独差分になる
- fixture generatorを作った時点でI3_VALIDになる

## MAINLINE-USEFUL RESULT

Reference-onlyで利用可能:
- 次回controlled corpusの最小fixture specification
- material competing-hypothesis discriminator
- clean UV OFF/ON pair
- same-cardinality weight scalar pair
- aggregate-only intake contract

自動統合不可:
- semantic promotion
- Blender emit
- runtime policy
- RIO-26 state
- mainline branch mutation

## CONFIDENCE

- C-051 experiment design adequacy: VERY HIGH
- render-part current candidate: unchanged Level 4
- material slot-vs-used-partition distinction: OPEN
- UV presence relation: OPEN
- weight scalar representation: OPEN

## NEXT QUESTION

新しいC-051 `.csmc` aggregateが到着した場合のみ、preregistered contractで `material discriminator -> 3-object validation -> clean UV pair -> same-cardinality weight pair` の順に評価する。

それまでは既存13 fixtureの同じ問いを再解析しない。
