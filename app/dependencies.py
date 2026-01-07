from fastapi import Query, Depends
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.database import get_db as get_db_base
import os

SHARDING_ENABLED = os.getenv('SHARDING_ENABLED', 'false').lower() == 'true'


def get_common_query_params(
    skip: int = Query(0, ge=0, description="Кількість записів для пропуску"),
    limit: int = Query(10, ge=1, le=100, description="Максимальна кількість записів")
):
    """
    Загальні query параметри для пагінації
    """
    return {"skip": skip, "limit": limit}


def get_db_for_travel_plan(travel_plan_id: Optional[UUID] = None):
    """
    Отримує сесію БД для конкретного travel_plan_id (для шардування).
    """
    if SHARDING_ENABLED:
        from app.sharding import get_sharded_db
        db = get_sharded_db(travel_plan_id)
        try:
            yield db
        finally:
            db.close()
    else:
        db_gen = get_db_base()
        db = next(db_gen)
        try:
            yield db
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass


def make_db_dependency_for_travel_plan(travel_plan_id: UUID):
    """
    Створює dependency функцію для конкретного travel_plan_id.
    Використовується в Depends() для path параметрів.
    """
    def _get_db():
        return get_db_for_travel_plan(travel_plan_id)
    return _get_db


def get_db_for_list():
    """
    Отримує сесію БД для списків (використовує перший шард або звичайну БД).
    """
    if SHARDING_ENABLED:
        from app.sharding import get_sharding_manager
        manager = get_sharding_manager()
        db = manager.get_db_session('db_0')  # Використовуємо перший шард для списків
        try:
            yield db
        finally:
            db.close()
    else:
        db_gen = get_db_base()
        db = next(db_gen)
        try:
            yield db
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
