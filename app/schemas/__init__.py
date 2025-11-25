# Pydantic schemas для валідації даних
from app.schemas import travel_plan, location

# Вирішуємо forward references після імпорту всіх схем
from app.schemas.location import LocationResponse
travel_plan.TravelPlanWithLocations.model_rebuild()
