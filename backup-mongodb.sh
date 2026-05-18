#!/bin/bash
# GalaxyBot MongoDB Backup Script
# Usage: ./backup-mongodb.sh
# Keeps 7 days of daily backups by default

BACKUP_DIR="/home/kali/Desktop/backups/mongodb"
DAYS_TO_KEEP=7
MONGO_URI="mongodb://127.0.0.1:27017"
DATABASE="go2super"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting MongoDB backup..."

mongodump --uri="$MONGO_URI" --db="$DATABASE" --out="$BACKUP_DIR/backup_$TIMESTAMP" --quiet

if [ $? -eq 0 ]; then
    echo "[$(date)] Backup completed: $BACKUP_DIR/backup_$TIMESTAMP"
    tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "backup_$TIMESTAMP" --remove-files
    echo "[$(date)] Compressed: backup_$TIMESTAMP.tar.gz"
else
    echo "[$(date)] ERROR: mongodump failed!"
    exit 1
fi

# Clean up old backups
find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f -mtime +$DAYS_TO_KEEP -delete
echo "[$(date)] Cleaned up backups older than $DAYS_TO_KEEP days"