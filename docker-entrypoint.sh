#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."
until pg_isready -h postgres -U ${DB_USER:-travel} -d ${DB_NAME:-travel_db} 2>/dev/null; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done

echo "PostgreSQL is ready!"

# Ініціалізуємо базу даних, якщо потрібно
echo "Initializing database..."
python -m app.db_init || echo "Database already initialized or initialization failed"

echo "Starting application..."
exec "$@"

