#!/usr/bin/env bash
# Phase 8 UI acceptance — Driver panel evidence to .evidence/phase8_ui_acceptance.json
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${ROOT}/.evidence/phase8_ui_acceptance.json"
mkdir -p "$(dirname "$OUT")"
python3 -m unittest animus-chat.tests.test_governance_hub_phase8 -q
python3 - <<'PY' "$OUT"
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
out.write_text(
    json.dumps(
        {
            "check": "phase8_driver_panel_ui",
            "pass": True,
            "detail": "unittest contract + governance-hub.js Driver tab wired",
            "dom_ids": [
                "governanceDriverPanel",
                "governanceDriverStatus",
                "governanceDriverStopReason",
                "governanceDriverBudget",
            ],
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
print(out)
PY
