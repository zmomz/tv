#!/bin/bash
set -e

BACKUP_DIR="backups"
TIMESTAMP=$(date +"%Y%m%d%H%M%S")
BACKUP_FILE="$BACKUP_DIR/tv_engine_backup_$TIMESTAMP.sql"

mkdir -p $BACKUP_DIR

echo "Creating database backup..."
docker compose exec -T db pg_dump -U tv_user -d tv_engine_db > $BACKUP_FILE

echo "Backup created at $BACKUP_FILE"
