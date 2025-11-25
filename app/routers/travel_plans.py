from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.models.travel_plan import TravelPlan
from app.schemas.travel_plan import TravelPlanCreate, TravelPlanUpdate, TravelPlanResponse, TravelPlanWithLocations
from app.schemas.location import LocationCreate, LocationResponse
from app.dependencies import get_common_query_params

router = APIRouter()


@router.get("/", response_model=List[TravelPlanResponse])
async def get_travel_plans(
    commons: dict = Depends(get_common_query_params),
    is_public: Optional[bool] = Query(None, description="Фільтр за публічністю"),
    db: Session = Depends(get_db)
):
    """
    Отримати список планів подорожей з пагінацією та фільтрацією
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
    Отримати план подорожі за ID з усіма локаціями
    """
    travel_plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
    if not travel_plan:
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
    Створити новий план подорожі
    """
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
    Оновити план подорожі за ID (з optimistic locking)
    """
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
    Видалити план подорожі за ID (локації будуть видалені автоматично через CASCADE)
    """
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
    Додати локацію до плану подорожі (auto-order)
    """
    from app.models.location import Location
    from app.schemas.location import LocationResponse
    
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

