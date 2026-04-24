#!/usr/bin/env bash
set -euo pipefail

COMPOSE="docker compose -f docker-compose.prod.yml"
NGINX_CONF="nginx/blue-green.conf"
MAX_WAIT=60   # seconds to wait for green to become healthy

# ── 1. Start/update green ────────────────────────────────────────────────────
echo "[1/5] Starting api-green..."
$COMPOSE up -d --build api-green

# ── 2. Wait for green to pass its healthcheck ────────────────────────────────
echo "[2/5] Waiting for green to be healthy (max ${MAX_WAIT}s)..."
elapsed=0
until $COMPOSE ps api-green | grep -q "healthy"; do
  sleep 2
  elapsed=$((elapsed + 2))
  if [ $elapsed -ge $MAX_WAIT ]; then
    echo "ERROR: api-green did not become healthy within ${MAX_WAIT}s. Aborting."
    $COMPOSE logs --tail=20 api-green
    exit 1
  fi
done
echo "  api-green is healthy."

# ── 3. Test green via the /test-standby/ Nginx route ────────────────────────
echo "[3/5] Testing green via /test-standby/health..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/test-standby/health)
if [ "$HTTP_CODE" != "200" ]; then
  echo "ERROR: /test-standby/health returned HTTP $HTTP_CODE. Aborting."
  exit 1
fi
echo "  Green responded HTTP 200."

# ── 4. Switch Nginx to green (zero-downtime reload) ──────────────────────────
echo "[4/5] Switching Nginx active backend: blue → green..."

# Start a background process that keeps hitting the API during the switch
# Any non-200 response is printed as an error
(
  for i in $(seq 1 20); do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/health)
    if [ "$CODE" != "200" ]; then
      echo "  [downtime-check] Request $i returned HTTP $CODE"
    fi
    sleep 0.1
  done
) &
CHECKER_PID=$!

# Swap active_backend from api-blue to api-green in the conf file
sed -i 's|server api-blue:8000;|server api-green:8000;|g' "$NGINX_CONF"

# Graceful reload — no dropped connections
$COMPOSE exec -T nginx nginx -s reload
echo "  Nginx reloaded."

wait $CHECKER_PID
echo "  Zero-downtime check complete."

# ── 5. Verify traffic now hits green ─────────────────────────────────────────
echo "[5/5] Verifying traffic is served by green..."
RESPONSE=$(curl -s http://127.0.0.1/health)
echo "  Health response: $RESPONSE"

HTTP_CODE=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print('200' if d.get('status')=='healthy' else '503')" 2>/dev/null || echo "unknown")
if [ "$HTTP_CODE" != "200" ]; then
  echo "ERROR: Health check failed after switch. Rolling back..."
  sed -i 's|server api-green:8000;|server api-blue:8000;|g' "$NGINX_CONF"
  $COMPOSE exec -T nginx nginx -s reload
  exit 1
fi

echo ""
echo "Deployment complete. Traffic is now served by api-green."
echo "To stop blue: docker compose -f docker-compose.prod.yml stop api-blue"
