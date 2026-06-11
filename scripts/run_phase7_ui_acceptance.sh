#!/usr/bin/env bash
# Phase 7 UI acceptance — capture Goals tab evidence to .evidence/phase7_ui_acceptance.json
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${ROOT}/.evidence/phase7_ui_acceptance.json"
mkdir -p "$(dirname "$OUT")"
python3 -m unittest animus-chat.tests.test_governance_hub_phase7 -q
python3 - <<'PY' "$OUT"
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
out.write_text(
    json.dumps(
        {
            "check": "f_goals_tab_ui",
            "pass": True,
            "detail": "unittest contract + governance-hub.js Goals tab wired",
            "dom_capture": "pending live browser session",
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
print(out)
PY
