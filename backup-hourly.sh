#!/bin/bash
set -e

SRVR_DIR="/var/www/vhosts/super.g/SRVRINSTALL"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "=== Hourly backup: ${TIMESTAMP} ==="

# Git snapshot (config changes)
cd "${SRVR_DIR}"
git add -A 2>/dev/null || true
if ! git diff --cached --quiet; then
  git commit -m "Hourly auto-backup ${TIMESTAMP}"
  log "Git commit created"
fi

# MongoDB dump (player data)
mongodump \
  --host 127.0.0.1:27017 \
  --username galaxybot \
  --password "Hak4oYk44ZahfRrepkFc" \
  --authenticationDatabase go2super \
  --db go2super \
  --out "/opt/galaxybot/backups/hourly-mongodb-${TIMESTAMP}" \
  --quiet

# Remove hourly dumps older than 48 hours
find /opt/galaxybot/backups -name "hourly-mongodb-*" -mtime +2 -exec rm -rf {} \; 2>/dev/null || true

# Offsite copy — dump user DB into git-tracked directory for GitHub push
rm -rf userdb_dump
mongodump \
  --host 127.0.0.1:27017 \
  --username galaxybot \
  --password "Hak4oYk44ZahfRrepkFc" \
  --authenticationDatabase go2super \
  --db go2super \
  --out ./userdb_dump_temp \
  --quiet
mv ./userdb_dump_temp/go2super ./userdb_dump
rm -rf ./userdb_dump_temp

git add -A
if ! git diff --cached --quiet; then
  git commit -m "USER DBASE"
  log "User database snapshot committed"
fi

# Push to GitHub
git push origin master 2>&1

log "=== Hourly backup complete ==="
