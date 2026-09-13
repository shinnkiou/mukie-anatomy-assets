"""Entry point for the fixed isolated CSMC canary self-update bootstrap."""
from __future__ import annotations

import json
import sys

try:
    from bridge.csmc_self_update import CsmcSelfUpdateError, run_cycle, self_test
except ModuleNotFoundError:
    from csmc_self_update import CsmcSelfUpdateError, run_cycle, self_test


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        if argv == ["self-test"]:
            result = self_test()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result.get("status") == "PASS" else 2
        if argv:
            print(json.dumps({"status":"ERROR","error_code":"CSMC_SELF_UPDATE_ARGS_REJECTED","error":"bootstrap runtime accepts no arguments"}, ensure_ascii=False), file=sys.stderr)
            return 2
        print(json.dumps(run_cycle(), ensure_ascii=False, indent=2))
        return 0
    except CsmcSelfUpdateError as exc:
        print(json.dumps({"status":"ERROR","error_code":exc.code,"error":str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except Exception as exc:
        print(json.dumps({"status":"ERROR","error_code":"CSMC_SELF_UPDATE_FAILED","error":str(exc),"error_type":type(exc).__name__}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
