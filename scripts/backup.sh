#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="$ROOT_DIR/data/research-manager/backups"
PAPERS_DIR="$ROOT_DIR/Paper"
MEMOS_DIR="$ROOT_DIR/Memo"
DATE_TAG="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BACKUP_DIR"

# DB backup through running postgres container
DB_DUMP_FILE="$BACKUP_DIR/postgres-$DATE_TAG.sql"
docker compose -f "$ROOT_DIR/compose.yaml" exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-paper_manager}" "${POSTGRES_DB:-paper_manager}" > "$DB_DUMP_FILE"

# PDF backup as tarball
if [[ -d "$PAPERS_DIR" ]]; then
  tar -czf "$BACKUP_DIR/papers-$DATE_TAG.tar.gz" -C "$PAPERS_DIR" .
fi

# Markdown notes and their metadata sidecars
if [[ -d "$MEMOS_DIR" ]]; then
  tar -czf "$BACKUP_DIR/memos-$DATE_TAG.tar.gz" -C "$MEMOS_DIR" .
fi

# Keep last 7 generations for each backup type
ls -1t "$BACKUP_DIR"/postgres-*.sql 2>/dev/null | tail -n +8 | xargs -r rm -f
ls -1t "$BACKUP_DIR"/papers-*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm -f
ls -1t "$BACKUP_DIR"/memos-*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm -f

echo "Backup completed: $DATE_TAG"
