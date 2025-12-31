#!/bin/bash

# Elsewedy Sentinel - Database Backup Script
# Usage: ./scripts/backup_db.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/db"
CONTAINER_NAME="sentinel_db"
DB_USER="postgres"

mkdir -p $BACKUP_DIR

echo "📦 Starting Backup for $CONTAINER_NAME..."

# Create Dump
docker exec -t $CONTAINER_NAME pg_dumpall -c -U $DB_USER > "$BACKUP_DIR/dump_$TIMESTAMP.sql"

if [ $? -eq 0 ]; then
    echo "✅ Backup Successful: $BACKUP_DIR/dump_$TIMESTAMP.sql"
    # Keep only last 7 backups
    ls -t $BACKUP_DIR/dump_*.sql | tail -n +8 | xargs -I {} rm {} 2>/dev/null
else
    echo "❌ Backup Failed!"
    exit 1
fi
