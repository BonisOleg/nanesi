#!/bin/sh
set -e

echo "Waiting for postgres..."
while ! nc -z "${POSTGRES_HOST:-db}" "${POSTGRES_PORT:-5432}"; do
  sleep 0.5
done
echo "PostgreSQL started"

exec "$@"
