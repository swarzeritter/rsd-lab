#!/bin/sh
set -e

echo "Waiting for master database to be ready..."
# Чекаємо поки master буде готовий та publication буде створено
DB_NAME="${POSTGRES_DB:-travel_db}"

# Чекаємо поки Master буде доступний
until PGPASSWORD=repuser psql -h postgres -U repuser -d "$DB_NAME" -c '\q' 2>/dev/null; do
  echo "Waiting for master database..."
  sleep 2
done

# Чекаємо поки publication буде створено
until PGPASSWORD=repuser psql -h postgres -U repuser -d "$DB_NAME" -c "SELECT 1 FROM pg_publication WHERE pubname = 'travel_planner_pub';" 2>/dev/null | grep -q 1; do
  echo "Waiting for master publication..."
  sleep 2
done

echo "Master database and publication are ready. Creating subscription..."

# Перевіряємо чи subscription вже існує
if psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_subscription WHERE subname = 'travel_planner_sub';" 2>/dev/null | grep -q 1; then
    echo "Subscription already exists, skipping creation."
else
    echo "Creating subscription..."
    # CREATE SUBSCRIPTION не може бути в DO блоці, тому виконуємо напряму
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "CREATE SUBSCRIPTION travel_planner_sub CONNECTION 'host=postgres port=5432 user=repuser password=repuser dbname=$DB_NAME' PUBLICATION travel_planner_pub;" || {
        echo "Warning: Failed to create subscription. It might already exist or there's a connection issue."
    }
    echo "Subscription created successfully."
fi
