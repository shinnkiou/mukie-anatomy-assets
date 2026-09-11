"""P0.18.1 wrapper: route worker pairing through the public app root.

Base44 public hosting can reject newly added SPA deep-links before BrowserRouter
loads. P0.18.1 keeps the worker transport unchanged but opens the guaranteed
root route with pairing query parameters instead of `/worker-pair`.
"""

from __future__ import annotations

import sys

try:
    from bridge import cli_p018 as inherited_cli
    from bridge import main as bridge_main
    from bridge import worker_transport
except ModuleNotFoundError:
    import cli_p018 as inherited_cli
    import main as bridge_main
    import worker_transport

BRIDGE_VERSION = "0.18.1-p0.18.1"
PAIRING_UI_URL = "https://sync-ops-base.base44.app/"

# The imported P0.18 functions resolve these module globals at call time.
worker_transport.PAIRING_UI_URL = PAIRING_UI_URL
worker_transport.WORKER_VERSION = BRIDGE_VERSION
inherited_cli.BRIDGE_VERSION = BRIDGE_VERSION
bridge_main.BRIDGE_VERSION = BRIDGE_VERSION


def main(argv: list[str] | None = None) -> int:
    return inherited_cli.main(sys.argv[1:] if argv is None else argv)


if __name__ == "__main__":
    raise SystemExit(main())
