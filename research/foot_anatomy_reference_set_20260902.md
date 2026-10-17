# BP3D Foot Anatomy Reference Set — 2026-09-02

Status: `REFERENCE_SET_READY_FOR_V01_1_QA`

This file records external anatomy references for the **derived visual layer only**. It does **not** change Final-v3/V45 canonical Face ownership.

Safety locks remain:
- anatomical front = `NEGATIVE_Y`
- MASTER/R7 write = 0
- Production14 = HOLD
- Production13 = FORBIDDEN
- rollback before V45 = forbidden
- canonical Face assignment change = 0

## References

### 1. OpenStax — Intrinsic Muscles of the Foot
- Source page: https://commons.wikimedia.org/wiki/File:1124_Intrinsic_Muscles_of_the_Foot.jpg
- Direct image: https://upload.wikimedia.org/wikipedia/commons/0/04/1124_Intrinsic_Muscles_of_the_Foot.jpg
- License: CC BY 4.0
- Author: OpenStax
- Use: dorsal superficial foot + plantar superficial/intermediate/deep muscle layers; extensor digitorum brevis, fibularis group, tibialis anterior, extensor hallucis/digitorum longus, abductor hallucis, flexor digitorum brevis, quadratus plantae, lumbricals.

### 2. Gray's Anatomy Plate 441
- Source page: https://commons.wikimedia.org/wiki/File:Gray441.png
- Direct image: https://upload.wikimedia.org/wikipedia/commons/8/8b/Gray441.png
- License: Public Domain
- Use: lateral/dorsal ankle-foot tendon routing, extensor retinaculum, fibularis/peroneal tendons, Achilles/tendocalcaneus, extensor digitorum brevis.

### 3. Gray's Anatomy Plate 442
- Source page: https://commons.wikimedia.org/wiki/File:Gray442.png
- Direct image: https://upload.wikimedia.org/wikipedia/commons/9/92/Gray442.png
- License: Public Domain
- Use: medial ankle-foot routing of tibialis anterior/posterior, flexor digitorum longus, flexor hallucis longus and Achilles.

### 4. Testut — Plantar Aponeurosis
- Source page: https://commons.wikimedia.org/wiki/File:PlantarAponeurosis.png
- Direct image: https://upload.wikimedia.org/wikipedia/commons/6/60/PlantarAponeurosis.png
- License: Public Domain / PDM
- Use: plantar aponeurosis direction, heel-to-forefoot tension path and plantar superficial context. Prevents painting the sole as a generic muscle mass.

### 5. Gray's Anatomy Plate 1241
- Source page: https://commons.wikimedia.org/wiki/File:Gray1241.png
- Direct image: https://upload.wikimedia.org/wikipedia/commons/5/5f/Gray1241.png
- License: Public Domain
- Use: lateral ankle tendon sheaths, fibularis longus/brevis routing, extensor tendons and heel connection.

### 6. Gray's Anatomy Plate 1242
- Source page: https://commons.wikimedia.org/wiki/File:Gray1242.png
- Direct image: https://upload.wikimedia.org/wikipedia/commons/2/2e/Gray1242.png
- License: Public Domain
- Use: medial ankle tendon sheaths, tibialis posterior, FDL, FHL, tibialis anterior and Achilles routing.

## BP3D V01.1 application order
1. Dorsum: OpenStax + Gray 441
2. Lateral ankle: Gray 441 + Gray 1241
3. Medial ankle: Gray 442 + Gray 1242
4. Plantar surface: OpenStax plantar layers + Testut plantar aponeurosis

## Constraints for V01.1
- Do not re-segment canonical semantics.
- Keep foot geography near-flat where surface muscle is not actually visible.
- Use tendon/retinaculum/bony-landmark transition weights around the ankle.
- Black lines are internal muscle boundaries only; do not outline the body perimeter or tendon fade perimeter.
- Do not promote a candidate without same-view QA, Drive readback and Supabase metrics.

Google Drive reference index: `1IY9Dud5mBzGxr7QkhMf_k_FRcED0TEIZBbjkmMkZmBA`
Google Drive reference folder: `1pUQwI7XzVQ6JVStmUzc4xO8bKHFuSAgp`
