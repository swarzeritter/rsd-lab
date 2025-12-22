#!/bin/bash
set -e

echo "========================================="
echo "Running post-init scripts..."
echo "========================================="

# Визначаємо хост залежно від контейнера
if [ "$HOSTNAME" = "travel_planner_db_init" ]; then
    DB_HOST="postgres"
elif [ "$HOSTNAME" = "travel_planner_replica_init" ]; then
    DB_HOST="postgres_sub"
else
    DB_HOST="localhost"
fi

# Чекаємо поки PostgreSQL буде готовий
until PGPASSWORD="${POSTGRES_PASSWORD:-travel}" pg_isready -h "$DB_HOST" -U "${POSTGRES_USER:-travel}" -d "${POSTGRES_DB:-travel_db}" > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL at $DB_HOST..."
  sleep 1
done

echo "PostgreSQL is ready at $DB_HOST!"

# Запускаємо міграції
if [ -d "/docker-entrypoint-migrations" ]; then
    echo "Running migrations..."
    for f in $(ls -1 /docker-entrypoint-migrations/*.sql 2>/dev/null | sort); do
        if [ -f "$f" ]; then
            echo "Executing migration: $(basename $f)"
            PGPASSWORD="${POSTGRES_PASSWORD:-travel}" psql -h "$DB_HOST" -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" < "$f" || echo "Migration already applied or error: $f"
        fi
    done
fi

# Запускаємо скрипти реплікації
if [ -d "/docker-entrypoint-replications" ]; then
    echo "Running replication scripts..."
    for f in $(ls -1 /docker-entrypoint-replications/*.sql 2>/dev/null | sort); do
        if [ -f "$f" ]; then
            echo "Executing replication script: $(basename $f)"
            PGPASSWORD="${POSTGRES_PASSWORD:-travel}" psql -h "$DB_HOST" -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" < "$f" || echo "Script already applied or error: $f"
        fi
    done
    
    for f in $(ls -1 /docker-entrypoint-replications/*.sh 2>/dev/null | sort); do
        if [ -f "$f" ]; then
            echo "Executing replication script: $(basename $f)"
            chmod +x "$f"
            bash "$f" || echo "Warning: Script $f returned non-zero exit code"
        fi
    done
fi

echo "========================================="
echo "Post-init scripts completed."
echo "========================================="

