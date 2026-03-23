#!/bin/sh
set -e
cd /app

python scripts/wait_for_postgres.py

if [ "${SKIP_DB_MIGRATIONS:-0}" != "1" ]; then
  echo "Running Alembic migrations…" >&2
  alembic upgrade head
fi

exec "$@"
