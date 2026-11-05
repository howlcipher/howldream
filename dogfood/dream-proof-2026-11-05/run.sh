#!/usr/bin/env bash
# Dream -> Proof -> Dream over the fixed Ruby Renaissance claims in ./inputs.
# Offline: no network, no model, no browser. Inputs are never modified.
set -euo pipefail
cd "$(dirname "$0")"
DREAM=${HOWLDREAM:-howldream}; PROOF=${HOWLPROOF:-howlproof}
OUT=outputs; rm -rf "$OUT"; mkdir -p "$OUT"

# 1. Dream clusters the externally authored thesis (records CLUSTERED, generates nothing).
$DREAM cluster --external inputs/ideas.json --out $OUT/discovery.json
UNIT=$(python3 -c "import json;print(json.load(open('$OUT/discovery.json'))['units'][0]['id'])")
$DREAM export $OUT/discovery.json --candidate-id "$UNIT" > $OUT/candidate.base.json

# 2. The claim author (not Dream) attaches the structured claims and the checks they grounded.
python3 - "$OUT" <<'PY'
import json, sys
out = sys.argv[1]
candidate = json.load(open(f"{out}/candidate.base.json"))
claims = json.load(open("inputs/claims.json"))
for claim in claims:
    claim["candidate_id"] = candidate["candidate_id"]
candidate["claims"] = claims
json.dump(candidate, open(f"{out}/candidate.json", "w"), indent=2)
PY

# 3. Supported handoff, then independent evaluation, then the return path.
$DREAM export-proof $OUT/candidate.json --evidence inputs/evidence.json --out $OUT/bundle
set +e
$PROOF evaluate $OUT/bundle --profile research --evidence-root $OUT/proof --json > $OUT/proof_result.json
echo "howlproof exit code: $?" > $OUT/proof_exit.txt
set -e
$DREAM import-proof --bundle $OUT/bundle --result $OUT/proof_result.json --out $OUT/assessment.json > /dev/null
python3 - "$OUT" <<'PY'
import json, sys
a = json.load(open(f"{sys.argv[1]}/assessment.json"))
print("candidate:", a["candidate_id"], "| status in export:",
      json.load(open(f"{sys.argv[1]}/candidate.json"))["status"])
print("disposition:", a["disposition"], "| confidence:", a["confidence"], "|", a["reason"])
print("proof verdict:", a["provenance"]["proof"]["verdict"], "(", a["provenance"]["proof"]["deciding_rule"], ")")
for row in a["evidence"]:
    print(f'{row["claim_status"]:30} {row["claim_id"]:20} {row["explanation"][:110]}')
PY
