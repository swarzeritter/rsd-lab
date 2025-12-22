#!/bin/bash
set -e

# Виконуємо стандартний entrypoint PostgreSQL
exec /docker-entrypoint.sh "$@"

