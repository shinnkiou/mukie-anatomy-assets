# CSMC Importer Hypothesis Lab v0.1

This path is an isolated, public-safe synthetic execution plane.

It does **not** contain:
- raw CSMC payload bytes
- proprietary MODELER binaries/decompiler dumps
- credentials
- production Worker control
- semantic promotion logic
- Blender export/emit logic

Run:

```bash
python tools/csmc_importer_lab/run_m1_acceptance.py
python -m unittest discover -s tools/csmc_importer_lab/tests -p "test_*.py" -v
```

M2 private evaluation is intentionally not implemented in this public path. The public Factory may consume only aggregate/hash/result packets from a separately controlled private evaluator.
