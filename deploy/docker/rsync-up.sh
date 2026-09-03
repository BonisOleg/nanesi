#!/usr/bin/env bash
# Перший залив коду на Droplet БЕЗ git (до появи remote).
# Usage:
#   ./deploy/docker/rsync-up.sh root@203.0.113.10
#   ./deploy/docker/rsync-up.sh malyar          # SSH Host alias → /var/www/malyar
#   REMOTE_PATH=/var/www/malyar ./deploy/docker/rsync-up.sh root@IP
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 user@host|ssh-alias"
  exit 1
fi

REMOTE_PATH="${REMOTE_PATH:-/var/www/malyar}"
SSH_IDENTITY="${SSH_IDENTITY:-$ROOT/malyar_do}"

RSYNC_RSH="ssh"
if [[ -f "$SSH_IDENTITY" ]]; then
  RSYNC_RSH="ssh -i $SSH_IDENTITY -o IdentitiesOnly=yes"
fi

echo "==> mkdir $TARGET:$REMOTE_PATH"
# shellcheck disable=SC2086
$RSYNC_RSH "$TARGET" "mkdir -p '$REMOTE_PATH'"

echo "==> rsync → $TARGET:$REMOTE_PATH"
rsync -avz --delete \
  -e "$RSYNC_RSH" \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude 'venv/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.env' \
  --exclude 'staticfiles/' \
  --exclude 'media/' \
  --exclude 'deploy/data/' \
  --exclude 'malyar_do' \
  --exclude 'postgres_data/' \
  --exclude '.DS_Store' \
  --exclude '_mockup/' \
  --exclude '_reference/' \
  "$ROOT/" "$TARGET:$REMOTE_PATH/"

echo "==> done. On server:"
echo "  ssh … && cd $REMOTE_PATH"
echo "  cp .env.docker.example .env && nano .env   # реальний IP замість DROPLET_IP"
echo "  bash deploy/docker/install-docker.sh"
echo "  bash deploy/docker/deploy.sh"
echo "  # з Mac: ./deploy/docker/sync-data.sh push $TARGET:$REMOTE_PATH --yes"
