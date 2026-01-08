from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from typing import List, Optional
from uuid import UUID, uuid4
import datetime
from app.database import get_db
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
    db: Session = Depends(get_db)
):
    """
    Отримати список локацій з пагінацією та фільтрацією.
    """
    skip = commons["skip"]
    limit = commons["limit"]
    
    # Якщо є travel_plan_id, то все просто
    if travel_plan_id:
        if SHARDING_ENABLED:
            # Треба отримати правильну сесію
            from app.dependencies import get_db_for_travel_plan
            db_gen = get_db_for_travel_plan(travel_plan_id)
            # Закриваємо поточну сесію, якщо вона не та
            db.close() 
            db = next(db_gen)
            
        try:
            plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
            if not plan:
                return []
            locations = plan.locations or []
            # Сортування і пагінація в пам'яті
            locations.sort(key=lambda x: x.get('visit_order', 0))
            return locations[skip : skip + limit]
        finally:
            if SHARDING_ENABLED:
                db.close()
                try:
                    next(db_gen)
                except StopIteration:
                    pass

    # Якщо немає travel_plan_id - скануємо всі плани (неефективно, але працює)
    # При шардуванні це поверне тільки з першого шарду (як і для планів)
    plans = db.query(TravelPlan).all()
    all_locations = []
    for p in plans:
        if p.locations:
            all_locations.extend(p.locations)
            
    # Сортування і пагінація
    # (Тут складно сортувати глобально, сортуємо по id для стабільності)
    all_locations.sort(key=lambda x: x.get('created_at', ''))
    
    return all_locations[skip : skip + limit]


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    travel_plan_id: Optional[UUID] = Query(None, description="ID плану подорожі (обов'язково при JSONB)"),
    db: Session = Depends(get_db)
):
    """
    Отримати локацію за ID. 
    УВАГА: Вимагає travel_plan_id, оскільки локації вкладені в плани.
    """
    if not travel_plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="travel_plan_id is required to find location in JSONB storage"
        )

    if SHARDING_ENABLED:
        db.close()
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
    
    try:
        plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
        if not plan or not plan.locations:
            raise HTTPException(status_code=404, detail="Location not found")
            
        location = next((l for l in plan.locations if l.get('id') == str(location_id)), None)
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
            
        return location
    finally:
        if SHARDING_ENABLED:
            db.close()
            try:
                next(db_gen)
            except StopIteration:
                pass


@router.post("/", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    location: LocationCreate,
    db: Session = Depends(get_db)
):
    """
    Створити нову локацію.
    """
    travel_plan_id = location.travel_plan_id
    
    if SHARDING_ENABLED:
        db.close()
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
        
    try:
        plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail=f"Travel plan {travel_plan_id} not found")
            
        # Підготовка даних
        loc_data = location.model_dump(exclude={'travel_plan_id'})
        loc_data['id'] = str(uuid4())
        loc_data['travel_plan_id'] = str(travel_plan_id)
        loc_data['created_at'] = datetime.datetime.now().isoformat()
        
        # Дати
        if loc_data.get('arrival_date'): loc_data['arrival_date'] = loc_data['arrival_date'].isoformat()
        if loc_data.get('departure_date'): loc_data['departure_date'] = loc_data['departure_date'].isoformat()
        
        # Decimal
        for field in ['latitude', 'longitude', 'budget']:
            if loc_data.get(field): loc_data[field] = float(loc_data[field])

        # Auto-order
        current_locations = list(plan.locations or [])
        if not loc_data.get('visit_order'):
            max_order = 0
            for l in current_locations:
                if l.get('visit_order', 0) > max_order:
                    max_order = l.get('visit_order')
            loc_data['visit_order'] = max_order + 1
            
        current_locations.append(loc_data)
        plan.locations = current_locations
        flag_modified(plan, "locations")
        
        db.commit()
        db.refresh(plan)
        
        return loc_data
    finally:
        if SHARDING_ENABLED:
            db.close()
            try:
                next(db_gen)
            except StopIteration:
                pass


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    location_update: LocationUpdate,
    travel_plan_id: Optional[UUID] = Query(None, description="ID плану подорожі"),
    db: Session = Depends(get_db)
):
    """
    Оновити локацію. Вимагає travel_plan_id.
    """
    if not travel_plan_id:
        raise HTTPException(status_code=400, detail="travel_plan_id required")

    if SHARDING_ENABLED:
        db.close()
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
        
    try:
        plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
            
        current_locations = list(plan.locations or [])
        idx = -1
        for i, l in enumerate(current_locations):
            if l.get('id') == str(location_id):
                idx = i
                break
        
        if idx == -1:
            raise HTTPException(status_code=404, detail="Location not found")
            
        # Update
        loc_data = current_locations[idx]
        update_data = location_update.model_dump(exclude_unset=True)
        
        # Конвертація типів
        for k, v in update_data.items():
            if isinstance(v, (datetime.date, datetime.datetime)):
                loc_data[k] = v.isoformat()
            elif isinstance(v, (int, float)):
                loc_data[k] = v
            elif hasattr(v, 'conjugate'): # Decimal
                loc_data[k] = float(v)
            else:
                loc_data[k] = v
                
        current_locations[idx] = loc_data
        plan.locations = current_locations
        flag_modified(plan, "locations")
        
        db.commit()
        return loc_data
    finally:
        if SHARDING_ENABLED:
            db.close()
            try:
                next(db_gen)
            except StopIteration:
                pass


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: UUID,
    travel_plan_id: Optional[UUID] = Query(None, description="ID плану подорожі"),
    db: Session = Depends(get_db)
):
    """
    Видалити локацію. Вимагає travel_plan_id.
    """
    if not travel_plan_id:
        raise HTTPException(status_code=400, detail="travel_plan_id required")

    if SHARDING_ENABLED:
        db.close()
        from app.dependencies import get_db_for_travel_plan
        db_gen = get_db_for_travel_plan(travel_plan_id)
        db = next(db_gen)
        
    try:
        plan = db.query(TravelPlan).filter(TravelPlan.id == travel_plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
            
        current_locations = list(plan.locations or [])
        new_locations = [l for l in current_locations if l.get('id') != str(location_id)]
        
        if len(new_locations) == len(current_locations):
            raise HTTPException(status_code=404, detail="Location not found")
            
        plan.locations = new_locations
        flag_modified(plan, "locations")
        
        db.commit()
        return None
    finally:
        if SHARDING_ENABLED:
            db.close()
            try:
                next(db_gen)
            except StopIteration:
                pass
