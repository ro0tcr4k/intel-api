#!/usr/bin/env bash
# Unpaid quote only. Does not spend USDC.
set -euo pipefail
BASE="${INTEL_URL:-https://intel.rootcrak.com}"
TARGET="${LIVE_SCAN_TARGET:-https://example.com}"

echo "== health =="
curl -sS "$BASE/v1/intel/health"
echo
echo "== sdk pin =="
curl -sS "$BASE/v1/intel/sdk"
echo
echo "== domain 402 =="
curl -sS -D - -o /tmp/intel-402.json -X POST "$BASE/v1/intel/scans/domain" \
  -H 'Content-Type: application/json' \
  -d "{\"target\":\"$TARGET\"}"
echo
python3 - <<'PY'
import json
body = json.load(open("/tmp/intel-402.json"))
detail = body.get("detail") or body
for row in detail.get("accepts") or []:
    extra = row.get("extra") or {}
    print({
        "rail": row.get("rail"),
        "network": row.get("network"),
        "price": row.get("price"),
        "amount": row.get("amount"),
        "pay_to": row.get("pay_to"),
        "feePayer": extra.get("feePayer"),
    })
PY
