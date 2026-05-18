#!/bin/bash
# GalaxyBot Server Health Check — run anytime: sudo bash healthcheck.sh
echo "=========================================="
echo "  GalaxyBot Health Check - $(date -u)"
echo "=========================================="

echo ""
echo "--- Services ---"
for s in galaxybot-mongod galaxybot-server galaxybot-wsbridge; do
    state=$(systemctl is-active "$s" 2>/dev/null)
    echo "  $s: $state"
done

echo ""
echo "--- Ports ---"
ss -tlnp 2>/dev/null | grep -E '9090|9091|5150|90 |27017|843' || echo "  (none listening)"

echo ""
echo "--- Memory ---"
free -h | grep -E "Mem|Swap"
echo "  Java RSS: $(ps -o rss= -p $(systemctl show -p MainPID galaxybot-server 2>/dev/null | cut -d= -f2) 2>/dev/null | awk '{printf "%.0f MB", $1/1024}')"

echo ""
echo "--- Disk ---"
df -h / | awk 'NR==2 {printf "  %s used of %s (%s)\n", $3, $2, $5}'
echo "  Logs: $(du -sh /opt/galaxybot/logs 2>/dev/null | cut -f1 || echo '0B')"

echo ""
echo "--- Login Test ---"
TOKEN=$(curl -s -m 5 http://localhost:9090/login/account \
  -X POST -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test1234"}' 2>/dev/null)
if echo "$TOKEN" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('code')==200 else 1)" 2>/dev/null; then
    echo "  Login: OK"
else
    echo "  Login: FAILED"
fi

echo ""
echo "--- Dashboard ---"
DBOARD=$(curl -s -m 5 -o /dev/null -w "%{http_code}" http://localhost:9090/dashboard.html 2>/dev/null)
echo "  Dashboard: HTTP $DBOARD"

echo ""
echo "--- MongoDB ---"
if mongosh --quiet --eval "db.runCommand({ping:1}).ok" 2>/dev/null | grep -q 1; then
    echo "  MongoDB ping: OK"
    echo "  Accounts: $(mongosh go2super --quiet --eval 'db.game_accounts.countDocuments()' 2>/dev/null || echo '?')"
else
    echo "  MongoDB: DOWN"
fi

echo ""
echo "--- Crossdomain ---"
printf '<policy-file-request/>\x00' | nc -w 2 127.0.0.1 843 2>/dev/null | grep -q "allow-access-from" && echo "  Port 843: OK" || echo "  Port 843: DOWN"

echo ""
echo "--- Recent Errors (24h) ---"
ERR=$(journalctl -u galaxybot-server --since "24 hours ago" --no-pager 2>/dev/null | grep -c "ERROR" 2>/dev/null)
echo "  Server errors (24h): $ERR"

echo ""
echo "=========================================="
echo "  Health Check Complete"
echo "=========================================="
