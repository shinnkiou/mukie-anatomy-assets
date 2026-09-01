# BP3D Non-Blender Completion Canon — 2026-09-01

Final-v3 full-body segmentation is now independently observed and physically split without requiring Blender as an execution gate.

- Production v4: 13,378 faces / 41 labels / 2,108 boundaries / 186 ordered cut paths / closed genus-0 manifold / mirror mismatch 0 / all Production faces observable in 42-direction proxy. Drive `1FQoDVi5C9td7NuAR6ESNN82rlv6Jlsrw`, SHA `ac5fd46e9e32cf086a1a51850a4a13a2de400caef600c36c9c71e727ee984aaf`.
- Detail observer v4.1: 56 labels / 2,368 boundaries / 127 pairs / 278 ordered toolpaths; evidence REVIEWED 11, ESTABLISHED_OR_PARENT 34, CONTEXT 7, HYPOTHESIS 4. Drive `1OTecFY_p5CWiT6Xi_mx-NCtuNrKx7bUU`, SHA `ea68812e6b49233b8a3ed5923d00186995db9ac2aa5fa8ef9971e05693302973`.
- Detail physical split v4.2: 56 individual OBJ files; 13,378 source Face IDs exactly once; duplicate/missing/extra 0/0/0; every split non-empty; all split non-manifold edge counts 0. Drive `1E4T3ec0M4cMgFaKSU_8FIY1J-l_joSEY`, SHA `99a0ee15924c84f94d2db6073700700191f9fbc0f1c3c3efe77e5ec5b8868c9c`.

The four face Detail hypotheses remain explicitly hypotheses and are not promoted by observation/splitting alone. Blender is optional only for final depth-buffer/material/lighting/deep-cavity visual cross-checks.

Safety: MASTER write 0 / R7 write 0 / Production14 write 0 / Production13 permanently forbidden.

Authoritative combined Drive canon: `13IwsZ_4mQP5O6c0Os0vYMVa3PpgbuDHR`.
