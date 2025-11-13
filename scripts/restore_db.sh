#!/bin/bash
set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <backup_file.sql>"
  exit 1
fi

BACKUP_FILE=$1

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: Backup file not found at $BACKUP_FILE"
  exit 1
fi

echo "Restoring database from $BACKUP_FILE..."
cat $BACKUP_FILE | docker compose exec -T db psql -U tv_user -d tv_engine_db

echo "Restore complete."
