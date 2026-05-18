#!/bin/bash
set -e

echo "=========================================="
echo "  GalaxyBot Server Installation"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
JAVA_VERSION="21"

# --- Check for root ---
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: This script must be run as root (sudo ./install.sh)"
    exit 1
fi

# --- Detect OS ---
if [ -f /etc/debian_version ]; then
    OS="debian"
elif [ -f /etc/redhat-release ]; then
    OS="redhat"
else
    echo "WARNING: Unsupported OS. Attempting Debian/Ubuntu commands."
    OS="debian"
fi

DEPS_DIR="$SCRIPT_DIR/deps"

# --- Install Java 21 ---
echo "[1/7] Installing Java 21..."
if command -v java &>/dev/null && java -version 2>&1 | grep -q "version \"21\."; then
    echo "  Java 21 already installed: $(java -version 2>&1 | head -1)"
else
    if ls "$DEPS_DIR"/openjdk-21-jre-headless*.deb 2>/dev/null; then
        echo "  Installing from local package..."
        dpkg -i "$DEPS_DIR"/openjdk-21-jre-headless*.deb 2>/dev/null || apt-get install -fy -qq
    elif [ "$OS" = "debian" ]; then
        apt-get update -qq
        apt-get install -y openjdk-21-jre-headless
    else
        yum install -y java-21-openjdk-headless
    fi
    echo "  Java 21 installed."
fi

# --- Install MongoDB 8.0 ---
echo "[2/7] Installing MongoDB 8.0..."
if command -v mongod &>/dev/null && mongod --version 2>&1 | grep -q "v8.0"; then
    echo "  MongoDB already installed: $(mongod --version 2>&1 | head -1)"
else
    if ls "$DEPS_DIR"/mongodb-org-server*.deb 2>/dev/null; then
        echo "  Installing from local packages..."
        dpkg -i "$DEPS_DIR"/mongodb-mongosh*.deb 2>/dev/null || true
        dpkg -i "$DEPS_DIR"/mongodb-org-server*.deb "$DEPS_DIR"/mongodb-org-mongos*.deb "$DEPS_DIR"/mongodb-org-shell*.deb "$DEPS_DIR"/mongodb-org-database*.deb "$DEPS_DIR"/mongodb-org-database-tools-extra*.deb "$DEPS_DIR"/mongodb-org*.deb 2>/dev/null || apt-get install -fy -qq
    elif [ "$OS" = "debian" ]; then
        curl -fsSL https://www.mongodb.org/static/pgp/server-8.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg
        echo "deb [signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg] https://repo.mongodb.org/apt/debian bookworm/mongodb-org/8.0 main" > /etc/apt/sources.list.d/mongodb-org-8.0.list
        apt-get update -qq
        apt-get install -y mongodb-org
    else
        cat > /etc/yum.repos.d/mongodb-org-8.0.repo << 'REPOEOF'
[mongodb-org-8.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/8.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-8.0.asc
REPOEOF
        yum install -y mongodb-org
    fi
    echo "  MongoDB 8.0 installed."
fi

# --- Install ws-bridge dependencies ---
echo "[3/7] Installing ws-bridge dependencies..."
if command -v python3 &>/dev/null; then
    if ls "$DEPS_DIR"/python3-websockets*.deb 2>/dev/null; then
        dpkg -i "$DEPS_DIR"/python3-websockets*.deb 2>/dev/null || true
    else
        pip3 install websockets 2>/dev/null || apt-get install -y python3-websockets 2>/dev/null || true
    fi
    echo "  ws-bridge dependencies installed."
else
    echo "  ERROR: python3 not found. Install Python 3 first."
    exit 1
fi

# --- Copy service files ---
echo "[4/7] Installing service files..."
# Create galaxybot user if not exists
if ! id galaxybot &>/dev/null; then
    useradd -r -s /bin/false -d /opt/galaxybot galaxybot
    echo "  Created 'galaxybot' user."
fi
cp "$SCRIPT_DIR/galaxybot-server.service" /etc/systemd/system/
cp "$SCRIPT_DIR/galaxybot-mongod.service" /etc/systemd/system/
cp "$SCRIPT_DIR/galaxybot-wsbridge.service" /etc/systemd/system/

# --- Copy MongoDB config ---
cp "$SCRIPT_DIR/mongod.conf" /etc/mongod.conf
mkdir -p /data/db
chown -R mongodb:mongodb /data/db 2>/dev/null || true
mkdir -p /var/log/mongodb
chown -R mongodb:mongodb /var/log/mongodb 2>/dev/null || true

# --- Copy sysctl config ---
cp "$SCRIPT_DIR/99-galaxybot.conf" /etc/sysctl.d/
sysctl -p /etc/sysctl.d/99-galaxybot.conf 2>/dev/null || true

# --- Disable Transparent HugePages (MongoDB performance) ---
echo "[5/7] Configuring performance tuning..."
if [ ! -f /etc/systemd/system/disable-thp.service ]; then
    cat > /etc/systemd/system/disable-thp.service << 'EOF'
[Unit]
Description=Disable Transparent HugePages (THP)
Before=galaxybot-mongod.service galaxybot-server.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo never > /sys/kernel/mm/transparent_hugepage/enabled && echo never > /sys/kernel/mm/transparent_hugepage/defrag'

[Install]
WantedBy=multi-user.target
EOF
    systemctl enable disable-thp.service 2>/dev/null || true
    echo never > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true
    echo never > /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null || true
    echo "  THP disabled."
else
    echo "  THP already disabled."
fi

# --- Copy server files to /opt/galaxybot ---
echo "[6/7] Copying server files..."

# Detect Java 21 path
JAVA_HOME="/usr/lib/jvm/java-21-openjdk-amd64"
if [ ! -f "$JAVA_HOME/bin/java" ]; then
    JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java 2>/dev/null) 2>/dev/null) 2>/dev/null) 2>/dev/null) 2>/dev/null
    if [ ! -f "$JAVA_HOME/bin/java" ]; then
        JAVA_HOME=$(find /usr/lib/jvm -name "java-21*" -type d 2>/dev/null | head -1)
    fi
fi
echo "  Java 21 found at: $JAVA_HOME"

mkdir -p /opt/galaxybot
cp "$SCRIPT_DIR/game-server-0.8.1.jar" /opt/galaxybot/
cp "$SCRIPT_DIR/ws-bridge.py" /opt/galaxybot/
chmod +x /opt/galaxybot/ws-bridge.py

# Copy README to install target
cp "$SCRIPT_DIR/README.txt" /opt/galaxybot/ 2>/dev/null || true
cp "$SCRIPT_DIR/READTHISFIRST.TXT" /opt/galaxybot/ 2>/dev/null || true

chown -R galaxybot:galaxybot /opt/galaxybot 2>/dev/null || true

# Update service file with detected Java path
sed -i "s|/usr/lib/jvm/java-21-openjdk-amd64|$JAVA_HOME|g" /etc/systemd/system/galaxybot-server.service

# --- Enable and prepare services ---
echo "[7/7] Enabling services..."
systemctl daemon-reload
systemctl enable galaxybot-mongod
systemctl enable galaxybot-server
systemctl enable galaxybot-wsbridge

# --- Create MongoDB user for auth ---
if [ -n "$GALAXYBOT_DB_PASSWORD" ]; then
    echo ""
    echo "  Creating MongoDB user..."
    systemctl start galaxybot-mongod 2>/dev/null || true
    sleep 3
    mongosh go2super --quiet --eval "
        db.createUser({
            user: 'galaxybot',
            pwd: '$GALAXYBOT_DB_PASSWORD',
            roles: ['readWrite']
        });
    " 2>/dev/null && echo "  MongoDB user 'galaxybot' created." || echo "  WARNING: Could not create MongoDB user (may already exist or MongoDB not ready)"
    # Update the service file with the password
    sed -i "s|GALAXYBOT_DB_PASSWORD=changeme|GALAXYBOT_DB_PASSWORD=$GALAXYBOT_DB_PASSWORD|g" /etc/systemd/system/galaxybot-server.service
    systemctl daemon-reload
fi

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "  Server files:  /opt/galaxybot/"
echo "  Game port:     9090 (HTTP REST + Dashboard)"
echo "  Game login:    5150 (TCP)"
echo "  Game world:    90 (TCP)"
echo "  WS bridge:     9091 (WebSocket)"
echo ""
echo "  Dashboard:     http://<server-ip>:9090/dashboard.html"
echo "  Admin login:   admin@supergo2.com"
echo "  Admin password: Set via GALAXYBOT_ADMIN_PASSWORD env var"
echo "                 (default: Ff5E!68a*5on)"
echo ""
echo "  To start:      sudo ./start.sh"
echo "  To stop:       sudo ./stop.sh"
echo ""
echo "  NOTE: MongoDB 8.0 may need the custom galaxybot-mongod service"
echo "        due to kernel compatibility. Default mongod.service may fail."
echo "  NOTE: THP (Transparent HugePages) has been disabled for best"
echo "        performance with Java + MongoDB."