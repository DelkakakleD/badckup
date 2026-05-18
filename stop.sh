#!/bin/bash

echo "Stopping GalaxyBot services..."

echo "  [1/3] Stopping WS Bridge..."
sudo systemctl stop galaxybot-wsbridge

echo "  [2/3] Stopping Game Server..."
sudo systemctl stop galaxybot-server

echo "  [3/3] Stopping MongoDB..."
# Try systemd first, then direct
sudo systemctl stop galaxybot-mongod 2>/dev/null
sleep 2
sudo pkill mongod 2>/dev/null
sleep 2

echo ""
echo "All services stopped."
echo ""
echo "Status:"
echo "  MongoDB:  $(ss -tlnp 2>/dev/null | grep -q ':27017 ' && echo 'still running' || echo 'stopped')"
echo "  Server:   $(systemctl is-active galaxybot-server 2>/dev/null || echo 'inactive')"
echo "  Bridge:   $(systemctl is-active galaxybot-wsbridge 2>/dev/null || echo 'inactive')"
