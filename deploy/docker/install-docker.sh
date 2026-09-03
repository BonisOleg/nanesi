#!/usr/bin/env bash
set -euo pipefail

if command -v docker >/dev/null 2>&1; then
  echo "Docker already installed: $(docker --version)"
  docker compose version
  exit 0
fi

curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

if ! groups "${SUDO_USER:-$USER}" | grep -q docker; then
  usermod -aG docker "${SUDO_USER:-$USER}" || true
  echo "Користувача додано до групи docker — може знадобитися re-login."
fi

docker compose version
