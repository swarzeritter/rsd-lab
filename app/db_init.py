"""
Скрипт для ініціалізації бази даних та створення таблиць
"""
import sys
from pathlib import Path

# Додаємо кореневу директорію проекту до Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import engine, Base
from app.models import TravelPlan, Location
from sqlalchemy import text


def create_trigger_function():
    """
    Створює функцію та тригер для автоматичного оновлення updated_at та version
    """
    trigger_function_sql = """
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        -- Опціонально: інкремент версії при кожному оновленні
        NEW.version = OLD.version + 1; 
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """
    
    trigger_sql = """
    DROP TRIGGER IF EXISTS update_travel_plans_modtime ON travel_plans;
    CREATE TRIGGER update_travel_plans_modtime
    BEFORE UPDATE ON travel_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
    """
    
    return trigger_function_sql, trigger_sql


def init_db():
    """
    Створює всі таблиці в базі даних, функції та тригери
    """
    try:
        print("Спроба підключення до бази даних...")
        
        # Створюємо таблиці
        Base.metadata.create_all(bind=engine)
        print("[OK] Створено таблиці: travel_plans, locations")
        
        # Створюємо функцію та тригер для updated_at
        with engine.begin() as conn:
            trigger_function_sql, trigger_sql = create_trigger_function()
            
            # Створюємо функцію
            conn.execute(text(trigger_function_sql))
            print("[OK] Створено функцію update_updated_at_column()")
            
            # Створюємо тригер
            conn.execute(text(trigger_sql))
            print("[OK] Створено тригер update_travel_plans_modtime")
        
        print("[OK] База даних успішно ініціалізована!")
        print("[OK] Всі таблиці, constraints, індекси та тригери створені")
        
    except Exception as e:
        print(f"[ERROR] Помилка ініціалізації бази даних: {e}")
        print("\nПеревірте:")
        print("1. Чи запущений PostgreSQL сервер")
        print("2. Чи правильний DATABASE_URL в .env файлі")
        print("3. Чи існує база даних")
        print("4. Чи правильний пароль користувача")
        sys.exit(1)


if __name__ == "__main__":
    init_db()

