#!/bin/bash

DB_USER="${GALAXYBOT_DB_USER:-galaxybot}"
DB_PASS="${GALAXYBOT_DB_PASSWORD:-Hak4oYk44ZahfRrepkFc}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Starting GalaxyBot services..."

# 1) MongoDB (via systemd)
echo "  [1/3] Starting MongoDB..."
sudo systemctl start galaxybot-mongod

# Wait for MongoDB to be ready (max 30s, with fallback to no-auth mode)
echo -n "  Waiting for MongoDB..."
MONGO_AUTH="--username $DB_USER --password $DB_PASS"
for i in $(seq 1 30); do
    if mongosh $MONGO_AUTH --quiet --eval "db.runCommand({ping:1})" &>/dev/null 2>&1; then
        echo " ready!"
        break
    fi
    # If auth fails, try without auth (may have been started without it)
    if mongosh --quiet --eval "db.runCommand({ping:1})" &>/dev/null 2>&1; then
        echo -n " (no auth, running fix-mongo.sh...)"
        if [ -f "$SCRIPT_DIR/fix-mongo.sh" ]; then
            sudo bash "$SCRIPT_DIR/fix-mongo.sh" && echo " ready!" && break
        fi
    fi
    echo -n "."
    sleep 1
done

# 1.5) Pre-flight account integrity check
echo "  [1.5/4] Checking account integrity..."
if [ -f "$SCRIPT_DIR/check-accounts.sh" ]; then
    sudo bash "$SCRIPT_DIR/check-accounts.sh"
fi

# 2) Game Server
echo "  [2/4] Starting Game Server..."
sudo systemctl start galaxybot-server

# Wait for server to be ready (max 120s)
echo -n "  Waiting for game server..."
for i in $(seq 1 120); do
    if ss -tlnp 2>/dev/null | grep -q ':9090 '; then
        echo " ready!"
        break
    fi
    echo -n "."
    sleep 1
done

# 3) WS Bridge
echo "  [3/4] Starting WS Bridge..."
sudo systemctl start galaxybot-wsbridge
sleep 2

# Verify
echo ""
echo "Checking services..."
echo "  MongoDB:  $(ss -tlnp 2>/dev/null | grep -q ':27017 ' && echo 'running' || echo 'DOWN')"
echo "  Server:   $(systemctl is-active galaxybot-server 2>/dev/null || echo 'DOWN')"
echo "  Bridge:   $(systemctl is-active galaxybot-wsbridge 2>/dev/null || echo 'DOWN')"

echo ""
echo "Listening ports:"
ss -tlnp 2>/dev/null | grep -E '9090|9091|5150|90 |27017' || netstat -tlnp 2>/dev/null | grep -E '9090|9091|5150|90|27017'

echo ""
echo "Server started. Dashboard: http://localhost:9090/dashboard.html"
