"""
Скрипт для перестворення таблиць з правильною структурою
ВИКОРИСТОВУЙТЕ ОБЕРЕЖНО: видаляє всі дані!
"""
import sys
from pathlib import Path

# Додаємо кореневу директорію проекту до Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.database import engine, Base
from app.models import TravelPlan, Location
from sqlalchemy import text


def recreate_tables():
    """
    Видаляє та перестворює всі таблиці з правильною структурою
    """
    try:
        print("Попередження: Цей скрипт видалить всі дані!")
        print("Продовжити? (yes/no): ", end="")
        response = input().strip().lower()
        
        if response != 'yes':
            print("Скасовано.")
            return
        
        print("\nПідключення до бази даних...")
        
        with engine.connect() as conn:
            # Видаляємо таблиці (у правильному порядку через foreign keys)
            print("Видалення старих таблиць...")
            conn.execute(text("DROP TABLE IF EXISTS locations CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS travel_plans CASCADE;"))
            conn.execute(text("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;"))
            conn.commit()
            print("[OK] Старі таблиці видалено")
        
        # Створюємо таблиці заново
        print("Створення нових таблиць...")
        Base.metadata.create_all(bind=engine)
        print("[OK] Створено таблиці: travel_plans, locations")
        
        # Створюємо функцію та тригер
        with engine.connect() as conn:
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
            CREATE TRIGGER update_travel_plans_modtime
            BEFORE UPDATE ON travel_plans
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
            """
            
            conn.execute(text(trigger_function_sql))
            conn.commit()
            print("[OK] Створено функцію update_updated_at_column()")
            
            conn.execute(text(trigger_sql))
            conn.commit()
            print("[OK] Створено тригер update_travel_plans_modtime")
        
        print("\n[OK] База даних успішно перестворена!")
        print("[OK] Всі таблиці, constraints, індекси та тригери створені правильно")
        
    except Exception as e:
        print(f"\n[ERROR] Помилка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    recreate_tables()

