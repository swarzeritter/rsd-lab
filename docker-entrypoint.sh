#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."
# Використовуємо DB_HOST з оточення або postgres за замовчуванням
DB_HOST=${DB_HOST:-postgres}
until pg_isready -h "$DB_HOST" -U ${DB_USER:-travel} 2>/dev/null; do
  echo "Waiting for PostgreSQL ($DB_HOST)..."
  sleep 1
done

echo "PostgreSQL is ready!"

# Ініціалізуємо базу даних, якщо потрібно
echo "Initializing database..."
python -m app.db_init || echo "Database already initialized or initialization failed"

echo "Starting application..."
exec "$@"

