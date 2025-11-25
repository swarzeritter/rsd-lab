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
├── tests/                # Тести API (Hurl файли)
│   ├── crud.hurl
│   ├── management.hurl
│   ├── race-conditions.hurl
│   ├── validation.hurl
│   └── variables.properties
├── main.py               # Точка входу
├── recreate_tables.py    # Скрипт для перестворення таблиць
├── requirements.txt      # Залежності
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

```bash
uvicorn main:app --reload
```

Сервер буде доступний за адресою: `http://127.0.0.1:8000`

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
