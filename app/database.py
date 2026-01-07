from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import os

# Перевірка чи увімкнено шардування
SHARDING_ENABLED = os.getenv('SHARDING_ENABLED', 'false').lower() == 'true'

# Завжди створюємо Base
Base = declarative_base()

# Ініціалізуємо звичайне підключення (за замовчуванням)
DATABASE_URL = getattr(settings, 'DATABASE_URL', 'postgresql://user:password@localhost/travel_db')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

SQLALCHEMY_DATABASE_URL = DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    echo=True,  # Для відлагодження SQL запитів
    connect_args={
        "connect_timeout": 10
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Якщо шардування увімкнено, спробуємо ініціалізувати
if SHARDING_ENABLED:
    try:
        from app.sharding import get_sharding_manager
        _ = get_sharding_manager()
    except Exception as e:
        print(f"Warning: Failed to initialize sharding manager: {e}")
        print("Falling back to single database mode")
        SHARDING_ENABLED = False


# Dependency для отримання сесії БД
def get_db():
    """
    Отримує сесію БД для звичайного режиму (без шардування).
    Для шардування використовуйте get_db_for_travel_plan з app.dependencies.
    """
    if not SHARDING_ENABLED:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        # Якщо шардування увімкнено, але викликається get_db - використовуємо перший шард
        from app.sharding import get_sharding_manager
        manager = get_sharding_manager()
        db = manager.get_db_session('db_0')
        try:
            yield db
        finally:
            db.close()

