#!/usr/bin/env bash
# Production deploy on DigitalOcean Droplet (HTTP-first).
# Usage on server: bash deploy/docker/deploy.sh
# Requires .env (from .env.docker.example). Always builds images.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)
SERVICES=(db backend nginx)

free_host_ports() {
  if command -v systemctl >/dev/null 2>&1; then
    systemctl stop nginx 2>/dev/null || true
    systemctl disable nginx 2>/dev/null || true
    for svc in $(systemctl list-units --type=service --all 2>/dev/null | grep -oE 'gunicorn[^ ]*' || true); do
      systemctl stop "$svc" 2>/dev/null || true
      systemctl disable "$svc" 2>/dev/null || true
    done
  fi
}

backend_healthz_ok() {
  "${COMPOSE[@]}" exec -T backend python3 -c \
    "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz/', timeout=5)" \
    >/dev/null 2>&1
}

if [[ ! -f .env ]]; then
  echo "FATAL: .env not found. cp .env.docker.example .env && nano .env"
  echo "Replace DROPLET_IP with real IPv4 before first browser hit."
  exit 1
fi

if grep -q 'DROPLET_IP' .env; then
  echo "FATAL: literal DROPLET_IP still in .env (ALLOWED_HOSTS/CSRF). Replace with real IPv4."
  exit 1
fi

echo "==> Freeing host ports 80/443"
free_host_ports

echo "==> stop nginx (уникнути 502 під час recreate backend)"
"${COMPOSE[@]}" stop nginx 2>/dev/null || true

echo "==> build + up db backend"
"${COMPOSE[@]}" up -d --build --remove-orphans db backend || true

echo "==> wait backend /healthz/ (up to ~4 min)"
ok=0
for _ in $(seq 1 80); do
  if backend_healthz_ok; then
    ok=1
    break
  fi
  sleep 3
done

if [[ "$ok" -ne 1 ]]; then
  echo "WARN: backend /healthz/ not ready — logs:"
  "${COMPOSE[@]}" logs --tail=50 backend db
  exit 1
fi

echo "==> start nginx"
"${COMPOSE[@]}" up -d --remove-orphans nginx || true

if curl -sf http://127.0.0.1/healthz/ >/dev/null; then
  echo "HTTP /healthz/ OK"
else
  echo "WARN: HTTP /healthz/ via nginx failed — ${COMPOSE[*]} logs backend nginx"
fi

echo "==> inventory"
missing=0
for svc in "${SERVICES[@]}"; do
  # Compose v2: "Up"; v5 інколи "running" — приймаємо обидва
  if "${COMPOSE[@]}" ps "$svc" 2>/dev/null | grep -qE "Up|running"; then
    echo "OK: $svc"
  else
    echo "MISSING: $svc"
    missing=1
  fi
done

"${COMPOSE[@]}" ps

if [[ "$missing" -ne 0 ]]; then
  echo "ERROR: some services not Up — check logs. Source of truth: curl /healthz/"
  exit 1
fi

echo "All ${#SERVICES[@]} services are running."
