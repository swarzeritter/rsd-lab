from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.models.location import Location
from app.models.travel_plan import TravelPlan
from app.schemas.location import LocationCreate, LocationUpdate, LocationResponse
from app.dependencies import get_common_query_params, get_db_for_travel_plan, get_db_for_list
import os

SHARDING_ENABLED = os.getenv('SHARDING_ENABLED', 'false').lower() == 'true'

router = APIRouter()


@router.get("/", response_model=List[LocationResponse])
async def get_locations(
    commons: dict = Depends(get_common_query_params),
    travel_plan_id: Optional[UUID] = Query(None, description="Фільтр за ID плану подорожі"),
):
    """
    Отримати список локацій з пагінацією та фільтрацією.
    При увімкненому шардуванні та наявності travel_plan_id використовує правильний шард.
    """
    skip = commons["skip"]
    limit = commons["limit"]
    
    # Отримуємо правильну сесію БД
    if SHARDING_ENABLED and travel_plan_id:
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
    else:
        from app.dependencies import get_db_for_list
        db_gen = get_db_for_list()
        db = next(db_gen)
    
    try:
        query = db.query(Location)
        
        if travel_plan_id:
            query = query.filter(Location.travel_plan_id == travel_plan_id)
        
        locations = query.order_by(Location.visit_order).offset(skip).limit(limit).all()
        return locations
    finally:
        db.close()
        try:
            next(db_gen)
        except StopIteration:
            pass


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    travel_plan_id: Optional[UUID] = Query(None, description="ID плану подорожі для визначення шарду"),
):
    """
    Отримати локацію за ID.
    При увімкненому шардуванні потрібен travel_plan_id для визначення шарду.
    """
    if SHARDING_ENABLED and not travel_plan_id:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "travel_plan_id parameter is required when sharding is enabled"}
        )
    
    # Отримуємо правильну сесію БД
    if SHARDING_ENABLED:
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
    else:
        from app.dependencies import get_db_for_list
        db_gen = get_db_for_list()
        db = next(db_gen)
    
    try:
        location = db.query(Location).filter(Location.id == location_id).first()
        if not location:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Location with ID {location_id} not found"}
            )
        return location
    finally:
        db.close()
        try:
            next(db_gen)
        except StopIteration:
            pass


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location: LocationCreate,
):
    """
    Створити нову локацію.
    При увімкненому шардуванні автоматично використовує правильний шард на основі travel_plan_id.
    """
    # Отримуємо правильну сесію БД
    if SHARDING_ENABLED:
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(location.travel_plan_id)
        db = next(db_gen)
    else:
        from app.dependencies import get_db_for_list
        db_gen = get_db_for_list()
        db = next(db_gen)
    
    try:
        # Перевірка існування travel_plan
        travel_plan = db.query(TravelPlan).filter(TravelPlan.id == location.travel_plan_id).first()
        if not travel_plan:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Travel plan with ID {location.travel_plan_id} not found"}
            )
        
        # Автоматичне призначення visit_order, якщо не вказано
        location_data = location.model_dump()
        if not location_data.get('visit_order'):
            max_order = db.query(func.max(Location.visit_order)).filter(
                Location.travel_plan_id == location.travel_plan_id
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


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    location_update: LocationUpdate,
    travel_plan_id: Optional[UUID] = Query(None, description="ID плану подорожі для визначення шарду"),
):
    """
    Оновити локацію за ID.
    При увімкненому шардуванні потрібен travel_plan_id для визначення шарду.
    """
    if SHARDING_ENABLED and not travel_plan_id:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "travel_plan_id parameter is required when sharding is enabled"}
        )
    
    # Отримуємо правильну сесію БД
    if SHARDING_ENABLED:
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
    else:
        from app.dependencies import get_db_for_list
        db_gen = get_db_for_list()
        db = next(db_gen)
    
    try:
        db_location = db.query(Location).filter(Location.id == location_id).first()
        if not db_location:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Location with ID {location_id} not found"}
            )
        
        update_data = location_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_location, field, value)
        
        db.commit()
        db.refresh(db_location)
        return db_location
    finally:
        db.close()
        try:
            next(db_gen)
        except StopIteration:
            pass


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID,
    travel_plan_id: Optional[UUID] = Query(None, description="ID плану подорожі для визначення шарду"),
):
    """
    Видалити локацію за ID.
    При увімкненому шардуванні потрібен travel_plan_id для визначення шарду.
    """
    if SHARDING_ENABLED and not travel_plan_id:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "travel_plan_id parameter is required when sharding is enabled"}
        )
    
    # Отримуємо правильну сесію БД
    if SHARDING_ENABLED:
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
    else:
        from app.dependencies import get_db_for_list
        db_gen = get_db_for_list()
        db = next(db_gen)
    
    try:
        db_location = db.query(Location).filter(Location.id == location_id).first()
        if not db_location:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"Location with ID {location_id} not found"}
            )
        
        db.delete(db_location)
        db.commit()
        return None
    finally:
        db.close()
        try:
            next(db_gen)
        except StopIteration:
            pass

