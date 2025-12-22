#!/bin/bash
set -e

# Цей скрипт виконується після ініціалізації PostgreSQL
# Він виконує міграції та налаштування реплікації

echo "========================================="
echo "PostgreSQL initialized, running custom scripts..."
echo "========================================="

# Запускаємо міграції
if [ -d "/docker-entrypoint-migrations" ]; then
    echo "Running migrations..."
    for f in $(ls -1 /docker-entrypoint-migrations/*.sql 2>/dev/null | sort); do
        if [ -f "$f" ]; then
            echo "Executing migration: $(basename $f)"
            psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" < "$f"
        fi
    done
fi

# Запускаємо скрипти реплікації
if [ -d "/docker-entrypoint-replications" ]; then
    echo "Running replication scripts..."
    for f in $(ls -1 /docker-entrypoint-replications/*.sql 2>/dev/null | sort); do
        if [ -f "$f" ]; then
            echo "Executing replication script: $(basename $f)"
            psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" < "$f"
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
echo "Custom scripts completed."
echo "========================================="

