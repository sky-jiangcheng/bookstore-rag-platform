#!/usr/bin/env bash
# Integration test for gateway -> agentic-rag flow
# Usage: TEST_JWT=<token> GATEWAY_URL=https://gateway.example.com/api/v1 ./integration_test.sh
set -euo pipefail
GATEWAY_URL=${GATEWAY_URL:-http://localhost:8000/api/v1}
TEST_JWT=${TEST_JWT:-}

echo "Using gateway: $GATEWAY_URL"

# 1. health
echo "CHECK: /health"
curl -s -o - -w "HTTP_RESPONSE:%{http_code}\n" "$GATEWAY_URL/health" || true

# 2. parse
echo "POST: parse requirements"
PARSE_RESP_FILE=$(mktemp)
curl -s -H "Content-Type: application/json" \
     ${TEST_JWT:+-H "Authorization: Bearer $TEST_JWT"} \
     -d '{"user_input":"推荐10本适合大学生的人工智能入门书","use_history":false}' \
     "$GATEWAY_URL/agent/parse" -o "$PARSE_RESP_FILE" -w "HTTP_PARSE:%{http_code}\n"
cat "$PARSE_RESP_FILE" | jq . || true
REQUEST_ID=$(jq -r .request_id // empty < "$PARSE_RESP_FILE" )
if [ -z "$REQUEST_ID" ]; then
  echo "No request_id returned from parse; aborting."
  exit 2
fi

echo "Got request_id: $REQUEST_ID"

# 3. generate
echo "POST: generate book list (limit=10)"
GEN_RESP_FILE=$(mktemp)
curl -s -H "Content-Type: application/json" \
     ${TEST_JWT:+-H "Authorization: Bearer $TEST_JWT"} \
     -d "{\"request_id\":\"$REQUEST_ID\",\"limit\":10}" \
     "$GATEWAY_URL/agent/generate" -o "$GEN_RESP_FILE" -w "HTTP_GENERATE:%{http_code}\n"
cat "$GEN_RESP_FILE" | jq . || true

# 4. summary
TOTAL=$(jq -r '.total_count // (.recommendations | length) // 0' < "$GEN_RESP_FILE" 2>/dev/null || echo 0)
echo "Generation total_count: $TOTAL"

# Save artifacts
OUT_DIR="./integration_test_output"
mkdir -p "$OUT_DIR"
mv "$PARSE_RESP_FILE" "$OUT_DIR/parse_response.json" || true
mv "$GEN_RESP_FILE" "$OUT_DIR/generate_response.json" || true

echo "Saved parse/generate responses to $OUT_DIR"

echo "Integration test finished"
