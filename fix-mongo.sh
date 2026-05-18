#!/bin/bash
# Fix MongoDB auth user and data issues
# Run once after install or whenever MongoDB auth breaks

DB_PASS="${GALAXYBOT_DB_PASSWORD:-Hak4oYk44ZahfRrepkFc}"
MONGO_CFG="/etc/mongod.conf"
LOG_PATH="/var/log/mongodb/mongod.log"
DB_PATH="/data/db"

echo "Fixing MongoDB..."

# 1) Stop everything
echo "  Stopping any running mongod..."
sudo systemctl stop galaxybot-server galaxybot-mongod 2>/dev/null
sudo pkill -9 mongod 2>/dev/null
sleep 2
rm -f "$DB_PATH/mongod.lock"

# 2) Start mongod WITHOUT auth
echo "  Starting MongoDB without auth..."
sudo /usr/bin/mongod --dbpath "$DB_PATH" --bind_ip 127.0.0.1 --port 27017 --fork --logpath "$LOG_PATH"
sleep 3

# 3) Drop + recreate galaxybot user
echo "  Creating galaxybot user..."
mongosh go2super --quiet --eval "
try { db.dropUser('galaxybot'); } catch(e) {}
db.createUser({ user: 'galaxybot', pwd: '$DB_PASS', roles: ['readWrite'] });
" && echo "  User created." || echo "  WARNING: User creation may have failed"

# 4) Fix old PLAYER rank -> USER
echo "  Fixing stale data..."
mongosh go2super --quiet --eval "
var r = db.game_accounts.updateMany({userRank: 'PLAYER'}, {\$set: {userRank: 'USER'}});
print('  Fixed ' + r.modifiedCount + ' account(s) with PLAYER rank');
" 2>/dev/null || true

# 5) Stop unauthed mongod and restart WITH auth
echo "  Restarting MongoDB WITH auth..."
sudo pkill mongod 2>/dev/null
sleep 2
sudo /usr/bin/mongod --config "$MONGO_CFG" --fork --logpath "$LOG_PATH"
sleep 3

# 6) Verify
echo "  Testing auth..."
if mongosh go2super -u galaxybot -p "$DB_PASS" --quiet --eval "db.runCommand({ping:1})" &>/dev/null; then
    echo "  MongoDB auth OK!"
else
    echo "  ERROR: Auth still failing. Check /var/log/mongodb/mongod.log"
    exit 1
fi

echo "  Updating service password..."
sudo sed -i "s|GALAXYBOT_DB_PASSWORD=.*|GALAXYBOT_DB_PASSWORD=$DB_PASS|" /etc/systemd/system/galaxybot-server.service
sudo systemctl daemon-reload

echo "Done. MongoDB is ready."
