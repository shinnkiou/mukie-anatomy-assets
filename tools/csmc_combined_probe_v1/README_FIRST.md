# CSMC Combined Probe V1

Read-only research helper for CSMC / CLIP STUDIO MODELER.

## Files
- 01_RUN_STATIC_SCAN.bat
- 02_STATIC_SCAN.ps1
- 03_RUN_RUNTIME_PROBE.bat
- 04_RUNTIME_PROBE.py
- 05_MODELER_GL_PROBE.js
- 06_INSTALL_FRIDA.bat

## Static scan
Drag a .csmc file onto 01_RUN_STATIC_SCAN.bat.
It checks CELSYS/package markers, FBX-like scene markers, glTF/GLB, COLLADA, PMX/MMD, generic rig words, and teacher fingerprints.

Output: %USERPROFILE%\CSMC_ANALYSIS\COMBINED_STATIC_SCAN_YYYYMMDD_HHMMSS\

Return SUMMARY.txt, SIGNATURE_HITS.tsv, SIMILARITY_EVIDENCE.tsv, TEACHER_FINGERPRINTS.tsv.

## Runtime probe
1. Close MODELER.
2. Run 06_INSTALL_FRIDA.bat once if needed.
3. Run 03_RUN_RUNTIME_PROBE.bat.
4. MODELER starts automatically.
5. Load the model and keep the camera fixed.
6. Do BASE -> L_ELBOW_FLEX -> BASE.
7. Return to the console and press Enter.

Known body VBO: 1,160,128 bytes = 36,254 vertices x 32 bytes.
Layout: Position float3 @0, Normal float3 @12, UV float2 @24.
Known EBO: 751,056 bytes.

Runtime output: %USERPROFILE%\CSMC_ANALYSIS\RUNTIME_VBO_PROBE_YYYYMMDD_HHMMSS\
Return SUMMARY.txt, RUNTIME_UPLOADS.tsv, BACKTRACES.txt.

No CSMC overwrite. No Ctrl+S automation. No serializer trigger. semantic_promotion=false.