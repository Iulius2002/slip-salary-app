#!/usr/bin/env bash
set -e

# If DATABASE_HOST/PORT provided, wait for DB
if [ -n "$DATABASE_HOST" ] && [ -n "$DATABASE_PORT" ]; then
  echo "Waiting for database $DATABASE_HOST:$DATABASE_PORT ..."
  until nc -z "$DATABASE_HOST" "$DATABASE_PORT"; do
    sleep 1
  done
  echo "Database is up."
fi

# Run migrations
alembic upgrade head

# Start API
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
