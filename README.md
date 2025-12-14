# Travel Plans API

FastAPI проект для управління планами подорожей та локаціями.

## Структура проекту

```
project1/
├── app/
│   ├── __init__.py
│   ├── config.py          # Конфігурація проекту
│   ├── database.py        # Підключення до БД
│   ├── db_init.py         # Скрипт ініціалізації БД
│   ├── dependencies.py    # Загальні залежності
│   ├── models/           # SQLAlchemy моделі
│   │   ├── travel_plan.py
│   │   └── location.py
│   ├── routers/          # API роутери
│   │   ├── travel_plans.py
│   │   └── locations.py
│   └── schemas/          # Pydantic схеми
│       ├── travel_plan.py
│       └── location.py
├── alembic/              # Міграції БД
├── tests/                # Тести API
│   ├── crud.hurl
│   ├── management.hurl
│   ├── race-conditions.hurl
│   ├── validation.hurl
│   ├── variables.properties
│   └── performance-tests/  # k6 тести продуктивності
│       ├── smoke-test.js
│       ├── load-test.js
│       ├── stress-test.js
│       ├── spike-test.js
│       ├── endurance-test.js
│       ├── config/
│       └── utils/
├── main.py               # Точка входу
├── recreate_tables.py    # Скрипт для перестворення таблиць
├── requirements.txt      # Залежності
├── Dockerfile            # Docker образ для додатку
├── docker-compose.yml    # Docker Compose конфігурація
├── docker-entrypoint.sh  # Скрипт ініціалізації для контейнера
├── env.example           # Приклад конфігураційного файлу
└── README.md            # Документація проекту
```

## Встановлення

1. Створіть віртуальне середовище:
```bash
python -m venv venv
```

2. Активуйте віртуальне середовище:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. Встановіть залежності:
```bash
pip install -r requirements.txt
```

4. Налаштуйте базу даних:
   - Створіть базу даних PostgreSQL з назвою `travel_db`
   - Оновіть `DATABASE_URL` в `app/config.py` або створіть файл `.env`:
   ```
   DATABASE_URL=postgresql://username:password@localhost/travel_db
   ```

5. Ініціалізуйте базу даних:
```bash
python app/db_init.py
```

Або використайте Alembic для міграцій:
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Запуск

### Нативний запуск

```bash
uvicorn main:app --reload
```

Сервер буде доступний за адресою: `http://127.0.0.1:8000`

### Запуск через Docker (рекомендовано)

Проект підтримує контейнеризацію через Docker та Docker Compose.

#### Вимоги

- Docker Desktop (Windows/Mac) або Docker Engine (Linux)
- Docker Compose v2.0+

#### Швидкий старт

1. **Створіть файл `.env`** (опціонально, можна використати значення за замовчуванням):
   ```bash
   cp env.example .env
   ```
   
   Або створіть `.env` з наступним вмістом:
   ```
   DB_NAME=travel_db
   DB_USER=travel
   DB_PASSWORD=travel
   DB_PORT=5432
   APP_PORT=8000
   ```

2. **Зберіть образи та запустіть контейнери**:
   ```bash
   docker compose up -d
   ```

3. **Перевірте статус контейнерів**:
   ```bash
   docker compose ps
   ```

4. **Сервер буде доступний за адресою**: `http://127.0.0.1:8000`

#### Корисні команди Docker

```bash
# Перегляд логів
docker compose logs -f app          # Логи додатку
docker compose logs -f postgres     # Логи бази даних

# Зупинка контейнерів
docker compose stop

# Запуск контейнерів
docker compose start

# Перезапуск контейнерів
docker compose restart

# Зупинка та видалення контейнерів
docker compose down

# Зупинка з видаленням volumes (видалить дані БД!)
docker compose down -v

# Перебудова образів
docker compose build

# Виконання команд в контейнері
docker compose exec app python -m app.db_init
docker compose exec postgres psql -U travel -d travel_db

# Перегляд використання ресурсів
docker stats
```

#### Структура Docker

- **Dockerfile**: Multi-stage build для оптимізації розміру образу
- **docker-compose.yml**: Оркестрація сервісів (PostgreSQL + FastAPI)
- **docker-entrypoint.sh**: Скрипт ініціалізації бази даних

#### Сервіси

- **postgres**: PostgreSQL 16-alpine база даних
  - Порт: 5432 (налаштовується через `DB_PORT`)
  - Дані зберігаються в volume `postgres_data`

- **app**: Travel Plans API додаток
  - Порт: 8000 (налаштовується через `APP_PORT`)
  - Автоматично чекає готовності PostgreSQL перед запуском
  - Автоматично ініціалізує базу даних при першому запуску

#### Health Checks

Обидва сервіси мають health checks:
- PostgreSQL: перевірка через `pg_isready`
- FastAPI: перевірка через `/health` endpoint

#### Тестування продуктивності з Docker

Після запуску контейнерів, тести k6 можна запускати з хоста:

```bash
# Smoke test
k6 run tests/performance-tests/smoke-test.js

# Load test
k6 run tests/performance-tests/load-test.js

# Всі тести
.\run-all-tests.ps1
```

API доступне на `localhost:8000`, тому тести працюють без додаткових налаштувань.

## Тестування

Проект використовує [Hurl](https://hurl.dev/) для тестування API.

### Встановлення Hurl

**Windows:**
```bash
choco install hurl
```
Або завантажте з [офіційного сайту](https://hurl.dev/docs/installation.html)

**Linux/Mac:**
```bash
curl -sSL https://install.hurl.dev | bash
```

### Запуск тестів

1. Переконайтеся, що сервер запущений:
```bash
uvicorn main:app --reload
```

2. В іншому терміналі запустіть тести:
```bash
# Windows
hurl --test tests\ --variables-file tests\variables.properties

# Linux/Mac
hurl --test tests/ --variables-file tests/variables.properties
```

### Результати тестування

Всі тести повинні пройти успішно:
- `crud.hurl` - тести CRUD операцій
- `management.hurl` - тести управління локаціями
- `race-conditions.hurl` - тести на race conditions та optimistic locking
- `validation.hurl` - тести валідації даних (31 тестовий сценарій)

## Тестування продуктивності (k6)

Проект також включає тести продуктивності з використанням [k6](https://k6.io/).

### Встановлення k6

**Windows:**
```bash
choco install k6
```
Або завантажте з [офіційного сайту](https://k6.io/docs/getting-started/installation/)

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

### Запуск тестів продуктивності

1. Переконайтеся, що сервер запущений (нативний або Docker)

2. Запустіть тести:
```bash
# Smoke test (базовий тест)
k6 run tests/performance-tests/smoke-test.js

# Load test (навантаження)
k6 run tests/performance-tests/load-test.js

# Stress test (стресове навантаження)
k6 run tests/performance-tests/stress-test.js

# Spike test (різкі зростання навантаження)
k6 run tests/performance-tests/spike-test.js

# Endurance test (тривале навантаження)
k6 run tests/performance-tests/endurance-test.js

# Всі тести (Windows PowerShell)
.\run-all-tests.ps1
```

3. Результати зберігаються в директорії `results/`

### Доступні тести

- **smoke-test.js**: Базовий тест для перевірки роботи API
- **load-test.js**: Тест навантаження (10-20 VUs)
- **stress-test.js**: Стрісове тестування (до 30 VUs)
- **spike-test.js**: Тест різких зростань навантаження (до 70 VUs)
- **endurance-test.js**: Тест тривалої роботи (10 VUs протягом 1 години)

## Документація API

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## API Endpoints

### Travel Plans (Плани подорожей)

- `GET /api/travel-plans/` - Отримати список планів подорожей
  - Query параметри: `skip`, `limit`, `is_public`
- `GET /api/travel-plans/{travel_plan_id}` - Отримати план подорожі за ID (з локаціями)
- `POST /api/travel-plans/` - Створити новий план подорожі
- `PUT /api/travel-plans/{travel_plan_id}` - Оновити план подорожі (з optimistic locking)
- `DELETE /api/travel-plans/{travel_plan_id}` - Видалити план подорожі
- `POST /api/travel-plans/{travel_plan_id}/locations` - Додати локацію до плану подорожі

### Locations (Локації)

- `GET /api/locations/` - Отримати список локацій
  - Query параметри: `skip`, `limit`, `travel_plan_id`
- `GET /api/locations/{location_id}` - Отримати локацію за ID
- `POST /api/locations/` - Створити нову локацію
- `PUT /api/locations/{location_id}` - Оновити локацію
- `DELETE /api/locations/{location_id}` - Видалити локацію

## Структура бази даних

### Таблиця `travel_plans`
- `id` (UUID, PK)
- `title` (VARCHAR(200), NOT NULL)
- `description` (TEXT)
- `start_date` (DATE)
- `end_date` (DATE, CHECK: end_date >= start_date)
- `budget` (DECIMAL(10,2), CHECK: budget >= 0)
- `currency` (VARCHAR(3), DEFAULT 'USD')
- `is_public` (BOOLEAN, DEFAULT FALSE)
- `version` (INTEGER, DEFAULT 1, optimistic lock)
- `created_at` (TIMESTAMPTZ)
- `updated_at` (TIMESTAMPTZ, auto-update)

### Таблиця `locations`
- `id` (UUID, PK)
- `travel_plan_id` (UUID, FK, CASCADE DELETE)
- `name` (VARCHAR(200), NOT NULL)
- `address` (TEXT)
- `latitude` (DECIMAL(10,6), CHECK: -90 <= latitude <= 90)
- `longitude` (DECIMAL(11,6), CHECK: -180 <= longitude <= 180)
- `visit_order` (INTEGER, NOT NULL, CHECK: visit_order > 0)
- `arrival_date` (TIMESTAMPTZ)
- `departure_date` (TIMESTAMPTZ, CHECK: departure_date >= arrival_date)
- `budget` (DECIMAL(10,2), CHECK: budget >= 0)
- `notes` (TEXT)
- `created_at` (TIMESTAMPTZ)

## Особливості реалізації

- ✅ Optimistic locking для travel_plans (поле version)
- ✅ CASCADE DELETE для locations при видаленні travel_plan
- ✅ Автоматичне призначення visit_order для нових локацій
- ✅ Валідація дат та координат
- ✅ Пагінація для всіх списків
- ✅ Фільтрація за різними параметрами
