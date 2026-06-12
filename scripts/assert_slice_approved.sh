#!/usr/bin/env bash
# Implementation-time guard: refuse to start slice work without verified plan approval.
# A plan is approved only when last_review.json shows APPROVED_FOR_IMPLEMENTATION
# (or APPROVED) for the active request — calling architect_review_plan is not approval.
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

architect_dir="$repo_root/.architect"
active_file="$architect_dir/active_request.json"
review_file="$architect_dir/last_review.json"
expected_request="${1:-}"

if [[ ! -f "$active_file" || ! -f "$review_file" ]]; then
  echo "assert-slice-approved: REFUSED — missing .architect/active_request.json or last_review.json" >&2
  echo "Run architect_start_request → architect_review_plan → verify APPROVED_FOR_IMPLEMENTATION before implementing." >&2
  exit 1
fi

python3 - <<'PY' "$active_file" "$review_file" "$expected_request"
import json, sys

active_path, review_path, expected = sys.argv[1:4]
active = json.load(open(active_path, encoding="utf-8"))
review = json.load(open(review_path, encoding="utf-8"))

request_id = str(active.get("request_id") or "").strip()
if not request_id:
    raise SystemExit("assert-slice-approved: REFUSED — active_request.json has no request_id")

if expected and expected != request_id:
    raise SystemExit(
        f"assert-slice-approved: REFUSED — active request {request_id!r} "
        f"does not match expected slice {expected!r}"
    )

if review.get("request_id") != request_id:
    raise SystemExit(
        f"assert-slice-approved: REFUSED — last_review request_id {review.get('request_id')!r} "
        f"does not match active {request_id!r}"
    )

if review.get("review_type") != "plan":
    raise SystemExit(
        f"assert-slice-approved: REFUSED — last_review review_type={review.get('review_type')!r}; "
        "need 'plan' (calling architect_review_plan is not approval — check status)"
    )

status = str(review.get("status") or "")
ok_statuses = {"APPROVED", "APPROVED_FOR_IMPLEMENTATION"}
if status not in ok_statuses:
    raise SystemExit(
        f"assert-slice-approved: REFUSED — plan gate status={status!r}; "
        f"need one of {sorted(ok_statuses)!r}"
    )

print(f"assert-slice-approved: OK request={request_id} plan={status}")
PY
