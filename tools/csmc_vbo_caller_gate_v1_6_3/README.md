# CSMC VBO CALLER GATE V1.6.3

V1.6.3 is a **completion pass** for the unfinished caller/backtrace gate already defined in V1.6.1.

It reuses the V1.6.2 validated BODY fingerprint and does not extend MemoryAccessMonitor page-watching.

Pipeline:

```
validated BODY upload
→ timestamp/thread/data pointer/hash
→ glBufferSubData return address/backtrace
→ MODELER RVA aggregation
→ stable stack signature
→ TARGET_RVAS.txt
→ stop
```

After a stable RVA is found, the next step is a **targeted Ghidra pass**, not V1.6.4 probe expansion.

See `GUIDE_JA.txt` before running.
