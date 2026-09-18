#!/usr/bin/env bash
# Let's Encrypt для nanesi.com.ua + www. Запуск на Droplet після git pull.
#   CERTBOT_EMAIL=you@domain bash deploy/docker/enable-https.sh
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

DOMAIN="nanesi.com.ua"
EMAIL="${CERTBOT_EMAIL:-}"
COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)

if [[ -z "$EMAIL" ]]; then
  echo "FATAL: CERTBOT_EMAIL=you@domain $0"
  exit 1
fi
if [[ ! -f .env ]]; then
  echo "FATAL: .env not found"
  exit 1
fi

echo "==> .env: hosts + HTTPS cookies (SECURE_SSL_REDIRECT лишається false)"
python3 - <<'PY'
from pathlib import Path
p = Path(".env")
lines = p.read_text().splitlines()
out = []
seen = set()
repl = {
    "ALLOWED_HOSTS": "nanesi.com.ua,www.nanesi.com.ua,46.101.212.242,127.0.0.1,localhost,backend,web",
    "CSRF_TRUSTED_ORIGINS": "https://nanesi.com.ua,https://www.nanesi.com.ua",
    "USE_HTTPS": "true",
    "SESSION_COOKIE_SECURE": "true",
    "CSRF_COOKIE_SECURE": "true",
    "SECURE_SSL_REDIRECT": "false",
    "CANONICAL_HOST": "nanesi.com.ua",
}
for line in lines:
    if not line or line.startswith("#") or "=" not in line:
        out.append(line)
        continue
    key = line.split("=", 1)[0]
    if key in repl:
        out.append(f"{key}={repl[key]}")
        seen.add(key)
    else:
        out.append(line)
for key, value in repl.items():
    if key not in seen:
        out.append(f"{key}={value}")
p.write_text("\n".join(out) + "\n")
print("OK .env")
PY

mkdir -p /var/www/certbot
if ! command -v certbot >/dev/null 2>&1; then
  apt-get update
  apt-get install -y certbot
fi

echo "==> nginx HTTP + ACME"
"${COMPOSE[@]}" up -d --build nginx
"${COMPOSE[@]}" exec -T backend true 2>/dev/null || "${COMPOSE[@]}" up -d backend

echo "==> certbot"
certbot certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN" -d "www.$DOMAIN" \
  --agree-tos -m "$EMAIL" --non-interactive --keep-until-expiring

if [[ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]]; then
  echo "FATAL: сертифікат не з’явився"
  exit 1
fi

echo "==> nginx TLS + backend env"
COMPOSE+=(-f docker-compose.https.yml)
"${COMPOSE[@]}" up -d --force-recreate --build nginx backend

echo "==> renew hook"
mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh <<'HOOK'
#!/usr/bin/env bash
cd /var/www/malyar
docker compose -f docker-compose.yml -f docker-compose.prod.yml -f docker-compose.https.yml exec -T nginx nginx -s reload
HOOK
chmod +x /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh

sleep 3
curl -sI -m 15 "https://$DOMAIN/healthz/" | head -8
echo "OK: https://$DOMAIN/"
