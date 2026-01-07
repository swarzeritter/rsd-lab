#!/bin/bash
set -e

# Створення баз даних на основі змінної оточення SHARD_DATABASES
# Формат: "db_0,db_1,db_2,db_3"

DB_USER="${POSTGRES_USER:-travel}"
DB_PASSWORD="${POSTGRES_PASSWORD:-travel}"

# Отримуємо список баз даних з змінної оточення
SHARD_DBS="${SHARD_DATABASES:-db_0,db_1,db_2,db_3}"

# Розбиваємо на масив
IFS=',' read -ra DB_NAMES <<< "$SHARD_DBS"

echo "Initializing databases: ${DB_NAMES[*]}"

# Створюємо бази даних
for db_name in "${DB_NAMES[@]}"; do
    db_name=$(echo "$db_name" | xargs)  # Trim whitespace
    echo "Creating database: $db_name"
    psql -v ON_ERROR_STOP=1 --username "$DB_USER" <<-EOSQL
        SELECT 'CREATE DATABASE $db_name'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$db_name')\gexec
EOSQL
done

# Застосовуємо міграції до кожної бази
if [ -d "/docker-entrypoint-migrations" ]; then
    for db_name in "${DB_NAMES[@]}"; do
        db_name=$(echo "$db_name" | xargs)  # Trim whitespace
        echo "Applying migrations to database: $db_name"
        for migration_file in /docker-entrypoint-migrations/*.sql; do
            if [ -f "$migration_file" ]; then
                echo "  Applying: $(basename $migration_file)"
                psql -v ON_ERROR_STOP=1 --username "$DB_USER" --dbname "$db_name" -f "$migration_file"
            fi
        done
    done
fi

echo "Database initialization completed for: ${DB_NAMES[*]}"

