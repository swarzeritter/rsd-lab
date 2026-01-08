from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from sqlalchemy.orm.attributes import flag_modified
from typing import List, Optional
from uuid import UUID, uuid4
import datetime
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
    Отримати план подорожі за ID з усіма локаціями (з JSONB).
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if SHARDING_ENABLED:
        db.close() # Close default session
        from app.sharding import get_sharded_db
        
        try:
            sharded_db = get_sharded_db(travel_plan_id)
            travel_plan = sharded_db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
            
            if not travel_plan:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"error": f"Travel plan with ID {travel_plan_id} not found"}
                )
            
            # Pydantic сам розбереться з JSONB списком у travel_plan.locations
            result = TravelPlanWithLocations.model_validate(travel_plan)
            return result
        finally:
            if 'sharded_db' in locals():
                sharded_db.close()
    else:
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
    Створити новий план подорожі.
    """
    plan_data = travel_plan.model_dump()
    
    # Ініціалізуємо порожній список локацій для JSONB
    if 'locations' not in plan_data:
        plan_data['locations'] = []
    
    if SHARDING_ENABLED:
        plan_id = uuid4()
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(plan_id)
        db = next(db_gen)
        try:
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
        db_travel_plan = TravelPlan(**plan_data)
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
    Оновити план подорожі за ID.
    """
    def _update(session, plan_id, update_schema):
        db_plan = session.query(TravelPlan).filter(TravelPlan.id == plan_id).first()
        if not db_plan:
            return None
            
        # Optimistic locking check
        if update_schema.version is not None and update_schema.version != db_plan.version:
             from fastapi.responses import JSONResponse
             return JSONResponse(
                 status_code=status.HTTP_409_CONFLICT,
                 content={
                     "error": "Conflict: Travel plan has been modified by another user",
                     "current_version": db_plan.version
                 }
             )

        update_data = update_schema.model_dump(exclude_unset=True, exclude={'version'})
        for field, value in update_data.items():
            setattr(db_plan, field, value)
            
        session.commit()
        session.refresh(db_plan)
        return db_plan

    if SHARDING_ENABLED:
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
        try:
            result = _update(db, travel_plan_id, travel_plan_update)
        finally:
            db.close()
    else:
        result = _update(db, travel_plan_id, travel_plan_update)

    if not result:
        raise HTTPException(status_code=404, detail="Travel plan not found")
    return result


@router.delete("/{travel_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_travel_plan(
    travel_plan_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Видалити план подорожі.
    """
    if SHARDING_ENABLED:
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
        try:
            db_plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
            if db_plan:
                db.delete(db_plan)
                db.commit()
        finally:
            db.close()
    else:
        db_plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
        if db_plan:
            db.delete(db_plan)
            db.commit()
    return None


@router.post("/{travel_plan_id}/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location_for_plan(
    travel_plan_id: UUID,
    location: LocationCreate,
    db: Session = Depends(get_db)
):
    """
    Додати локацію до плану подорожі (в JSONB список).
    """
    
    def _add_location(session, plan_id, loc_schema):
        db_plan = session.query(TravelPlan).filter(TravelPlan.id == plan_id).first()
        if not db_plan:
            return None
        
        # Готуємо дані локації
        loc_data = loc_schema.model_dump(exclude={'travel_plan_id'})
        loc_data['id'] = str(uuid4()) # Генеруємо ID тут
        loc_data['travel_plan_id'] = str(plan_id)
        loc_data['created_at'] = datetime.datetime.now().isoformat()
        
        # Серіалізуємо дати в стрічки (для JSON)
        if loc_data.get('arrival_date'):
            loc_data['arrival_date'] = loc_data['arrival_date'].isoformat()
        if loc_data.get('departure_date'):
             loc_data['departure_date'] = loc_data['departure_date'].isoformat()
        
        # Decimal to float/str
        if loc_data.get('latitude'): loc_data['latitude'] = float(loc_data['latitude'])
        if loc_data.get('longitude'): loc_data['longitude'] = float(loc_data['longitude'])
        if loc_data.get('budget'): loc_data['budget'] = float(loc_data['budget'])

        # Auto-order
        current_locations = db_plan.locations or []
        if not loc_data.get('visit_order'):
            max_order = 0
            for l in current_locations:
                if l.get('visit_order', 0) > max_order:
                    max_order = l.get('visit_order')
            loc_data['visit_order'] = max_order + 1
            
        # Додаємо в список
        # Важливо: SQLAlchemy потребує явного копіювання списку або flag_modified
        new_locations = list(current_locations)
        new_locations.append(loc_data)
        
        db_plan.locations = new_locations
        flag_modified(db_plan, "locations") # Сигналізуємо, що JSONB змінився
        
        session.commit()
        session.refresh(db_plan)
        return loc_data # Повертаємо словник, Pydantic з нього зробить LocationResponse

    if SHARDING_ENABLED:
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
        try:
            result = _add_location(db, travel_plan_id, location)
        finally:
            db.close()
    else:
        result = _add_location(db, travel_plan_id, location)
        
    if not result:
        raise HTTPException(status_code=404, detail="Travel plan not found")
        
    return result
