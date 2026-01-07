from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from uuid import UUID, uuid4
from app.database import get_db
from app.models.travel_plan import TravelPlan
from app.schemas.travel_plan import TravelPlanCreate, TravelPlanUpdate, TravelPlanResponse, TravelPlanWithLocations
from app.schemas.location import LocationCreate, LocationResponse
from app.dependencies import get_common_query_params, get_db_for_travel_plan, get_db_for_list
import os

SHARDING_ENABLED = os.getenv('SHARDING_ENABLED', 'false').lower() == 'true'

router = APIRouter()


@router.get("/", response_model=List[TravelPlanResponse])
async def get_travel_plans(
    commons: dict = Depends(get_common_query_params),
    is_public: Optional[bool] = Query(None, description="Фільтр за публічністю"),
    db: Session = Depends(get_db_for_list if SHARDING_ENABLED else get_db)
):
    """
    Отримати список планів подорожей з пагінацією та фільтрацією.
    При увімкненому шардуванні повертає дані тільки з першого шарду.
    """
    skip = commons["skip"]
    limit = commons["limit"]
    
    query = db.query(TravelPlan)
    
    if is_public is not None:
        query = query.filter(TravelPlan.is_public == is_public)
    
    travel_plans = query.offset(skip).limit(limit).all()
    return travel_plans


@router.get("/{travel_plan_id}", response_model=TravelPlanWithLocations)
async def get_travel_plan(
    travel_plan_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Отримати план подорожі за ID з усіма локаціями.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"GET travel_plan {travel_plan_id}, SHARDING_ENABLED={SHARDING_ENABLED}")

    if SHARDING_ENABLED:
        # Для шардування керуємо сесією вручну, щоб уникнути конфліктів
        # Закриваємо дефолтну сесію
        db.close()
        
        from app.sharding import get_sharded_db
        from sqlalchemy.orm import joinedload
        
        try:
            # Відкриваємо правильну сесію
            logger.info("Getting sharded DB session")
            sharded_db = get_sharded_db(travel_plan_id)
            
            # Використовуємо joinedload для завантаження пов'язаних даних
            logger.info("Executing query with joinedload")
            travel_plan = sharded_db.query(TravelPlan).options(joinedload(TravelPlan.locations)).filter(TravelPlan.id == travel_plan_id).first()
            
            if not travel_plan:
                logger.warning(f"Travel plan {travel_plan_id} not found")
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": f"Travel plan with ID {travel_plan_id} not found"}
                )
            
            logger.info("Converting ORM object to Pydantic model manually")
            # Примусово завантажуємо locations, якщо вони не завантажилися через joinedload
            # Це доступ до атрибуту, який викличе SQL запит, якщо сесія ще відкрита
            _ = travel_plan.locations
            
            # Конвертуємо в Pydantic модель
            result = TravelPlanWithLocations.model_validate(travel_plan)
            logger.info("Model validated successfully")
            return result
        except Exception as e:
            logger.error(f"Error in get_travel_plan: {e}", exc_info=True)
            raise
        finally:
            logger.info("Closing sharded session")
            if 'sharded_db' in locals():
                sharded_db.close()
    else:
        # Звичайний режим - використовуємо Depends і lazy loading (або joinedload)
        # Session закривається автоматично FastAPI
        logger.info("Using standard session")
        travel_plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
        if not travel_plan:
            logger.warning(f"Travel plan {travel_plan_id} not found")
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Travel plan with ID {travel_plan_id} not found"}
            )
        return travel_plan


@router.post("/", response_model=TravelPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_travel_plan(
    travel_plan: TravelPlanCreate,
    db: Session = Depends(get_db)
):
    """
    Створити новий план подорожі.
    При увімкненому шардуванні генерує UUID заздалегідь для визначення шарду.
    """
    if SHARDING_ENABLED:
        # Генеруємо UUID заздалегідь для визначення шарду
        plan_id = uuid4()
        
        # Отримуємо правильну сесію БД для цього ID
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(plan_id)
        db = next(db_gen)
        try:
            plan_data = travel_plan.model_dump()
            plan_data['id'] = plan_id
            db_travel_plan = TravelPlan(**plan_data)
            db.add(db_travel_plan)
            db.commit()
            db.refresh(db_travel_plan)
            return db_travel_plan
        finally:
            db.close()
            try:
                next(db_gen)
            except StopIteration:
                pass
    else:
        # Звичайний режим - використовуємо Depends
        db_travel_plan = TravelPlan(**travel_plan.model_dump())
        db.add(db_travel_plan)
        db.commit()
        db.refresh(db_travel_plan)
        return db_travel_plan


@router.put("/{travel_plan_id}", response_model=TravelPlanResponse)
async def update_travel_plan(
    travel_plan_id: UUID,
    travel_plan_update: TravelPlanUpdate,
    db: Session = Depends(get_db)
):
    """
    Оновити план подорожі за ID (з optimistic locking).
    При увімкненому шардуванні автоматично використовує правильний шард.
    """
    if SHARDING_ENABLED:
        # Отримуємо правильну сесію БД
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
        try:
            db_travel_plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
            if not db_travel_plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"План подорожі з ID {travel_plan_id} не знайдено"
                )
            
            # Optimistic locking перевірка
            if travel_plan_update.version is None:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Validation error: Version is required for update"}
                )
            
            if travel_plan_update.version != db_travel_plan.version:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={
                        "error": "Conflict: Travel plan has been modified by another user",
                        "current_version": db_travel_plan.version
                    }
                )
            
            # Виключаємо version з оновлення, бо його оновлює тригер автоматично
            update_data = travel_plan_update.model_dump(exclude_unset=True, exclude={'version'})
            for field, value in update_data.items():
                setattr(db_travel_plan, field, value)
            
            # Версія та updated_at оновлюються автоматично через тригер
            
            db.commit()
            db.refresh(db_travel_plan)
            return db_travel_plan
        finally:
            db.close()
            try:
                next(db_gen)
            except StopIteration:
                pass
    else:
        # Звичайний режим - використовуємо Depends
        db_travel_plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
        if not db_travel_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"План подорожі з ID {travel_plan_id} не знайдено"
            )
        
        # Optimistic locking перевірка
        if travel_plan_update.version is None:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Validation error: Version is required for update"}
            )
        
        if travel_plan_update.version != db_travel_plan.version:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "error": "Conflict: Travel plan has been modified by another user",
                    "current_version": db_travel_plan.version
                }
            )
        
        # Виключаємо version з оновлення, бо його оновлює тригер автоматично
        update_data = travel_plan_update.model_dump(exclude_unset=True, exclude={'version'})
        for field, value in update_data.items():
            setattr(db_travel_plan, field, value)
        
        # Версія та updated_at оновлюються автоматично через тригер
        
        db.commit()
        db.refresh(db_travel_plan)
        return db_travel_plan


@router.delete("/{travel_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_travel_plan(
    travel_plan_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Видалити план подорожі за ID (локації будуть видалені автоматично через CASCADE).
    При увімкненому шардуванні автоматично використовує правильний шард.
    """
    if SHARDING_ENABLED:
        # Отримуємо правильну сесію БД
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
        try:
            db_travel_plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
            if not db_travel_plan:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": f"Travel plan with ID {travel_plan_id} not found"}
                )
            
            db.delete(db_travel_plan)
            db.commit()
            return None
        finally:
            db.close()
            try:
                next(db_gen)
            except StopIteration:
                pass
    else:
        # Звичайний режим - використовуємо Depends
        db_travel_plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
        if not db_travel_plan:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Travel plan with ID {travel_plan_id} not found"}
            )
        
        db.delete(db_travel_plan)
        db.commit()
        return None


# Endpoint для створення локації в межах плану подорожі
@router.post("/{travel_plan_id}/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location_for_plan(
    travel_plan_id: UUID,
    location: LocationCreate,
    db: Session = Depends(get_db)
):
    """
    Додати локацію до плану подорожі (auto-order).
    При увімкненому шардуванні автоматично використовує правильний шард.
    """
    from app.models.location import Location
    from app.schemas.location import LocationResponse
    
    if SHARDING_ENABLED:
        # Отримуємо правильну сесію БД
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
        try:
            # Перевірка існування travel_plan
            travel_plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
            if not travel_plan:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": f"Travel plan with ID {travel_plan_id} not found"}
                )
            
            # Встановлюємо travel_plan_id з URL
            location_data = location.model_dump(exclude={'travel_plan_id'})
            location_data['travel_plan_id'] = travel_plan_id
            
            # Автоматичне призначення visit_order, якщо не вказано
            if not location_data.get('visit_order'):
                max_order = db.query(func.max(Location.visit_order)).filter(
                    Location.travel_plan_id == travel_plan_id
                ).scalar() or 0
                location_data['visit_order'] = max_order + 1
            
            db_location = Location(**location_data)
            db.add(db_location)
            db.commit()
            db.refresh(db_location)
            return db_location
        finally:
            db.close()
            try:
                next(db_gen)
            except StopIteration:
                pass
    else:
        # Звичайний режим - використовуємо Depends
        # Перевірка існування travel_plan
        travel_plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
        if not travel_plan:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Travel plan with ID {travel_plan_id} not found"}
            )
        
        # Встановлюємо travel_plan_id з URL
        location_data = location.model_dump(exclude={'travel_plan_id'})
        location_data['travel_plan_id'] = travel_plan_id
        
        # Автоматичне призначення visit_order, якщо не вказано
        if not location_data.get('visit_order'):
            max_order = db.query(func.max(Location.visit_order)).filter(
                Location.travel_plan_id == travel_plan_id
            ).scalar() or 0
            location_data['visit_order'] = max_order + 1
        
        db_location = Location(**location_data)
        db.add(db_location)
        db.commit()
        db.refresh(db_location)
        return db_location

