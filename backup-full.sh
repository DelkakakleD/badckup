#!/bin/bash
set -e

# ============================================================
# GalaxyBot Full Server Backup
# Backs up: git-tracked configs, MongoDB (player data),
#           systemd service files, server logs, JAR
# ============================================================

BACKUP_DIR="/opt/galaxybot/backups"
SRVR_DIR="/var/www/vhosts/super.g/SRVRINSTALL"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="galaxybot-full-${TIMESTAMP}"
RETENTION_DAYS=${RETENTION_DAYS:-7}
WORKDIR=$(mktemp -d)

cleanup() { rm -rf "$WORKDIR"; }
trap cleanup EXIT

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "=== Starting full backup: ${BACKUP_NAME} ==="

# ---- 1. Git snapshot ----
log "Committing config changes to git..."
cd "${SRVR_DIR}"
git add -A 2>/dev/null || true

if ! git diff --cached --quiet; then
  git commit -m "Auto-backup ${TIMESTAMP}"
  log "Git commit created"
else
  log "No config changes to commit"
fi

# ---- 2. MongoDB dump ----
log "Dumping MongoDB (go2super)..."
mongodump \
  --host 127.0.0.1:27017 \
  --username galaxybot \
  --password "Hak4oYk44ZahfRrepkFc" \
  --authenticationDatabase go2super \
  --db go2super \
  --out "${WORKDIR}/mongodb" \
  --quiet
log "MongoDB dump complete ($(du -sh "${WORKDIR}/mongodb" | cut -f1))"

# ---- 3. Systemd service files ----
mkdir -p "${WORKDIR}/systemd"
cp /etc/systemd/system/galaxybot-*.service "${WORKDIR}/systemd/" 2>/dev/null || true

# ---- 4. Server logs (last 7 days) ----
mkdir -p "${WORKDIR}/logs"
if [ -d /opt/galaxybot/logs ]; then
  find /opt/galaxybot/logs -name "*.log" -mtime -7 -exec cp {} "${WORKDIR}/logs/" \; 2>/dev/null || true
fi

# ---- 5. Copy current JAR ----
cp /opt/galaxybot/game-server-0.8.1.jar "${WORKDIR}/game-server-0.8.1.jar" 2>/dev/null || log "WARN: JAR copy failed"

# ---- 6. Clone git repo for offline reference ----
git clone "${SRVR_DIR}" "${WORKDIR}/config" 2>/dev/null || log "WARN: git clone failed"

# ---- 7. Package everything into one tarball ----
mkdir -p "${BACKUP_DIR}"
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" -C "${WORKDIR}" .
log "Packaged backup: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz ($(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1))"

# ---- 8. Remove backups older than retention period ----
find "${BACKUP_DIR}" -name "galaxybot-full-*.tar.gz" -mtime +"${RETENTION_DAYS}" -delete 2>/dev/null || true

# ---- 9. Push to remote if configured ----
if git remote -v | grep -q "origin"; then
  log "Pushing to remote..."
  cd "${SRVR_DIR}"
  git push origin master 2>&1 || log "WARN: git push failed (remote not configured or unreachable)"
fi

log "=== Backup complete: ${BACKUP_NAME} ==="
