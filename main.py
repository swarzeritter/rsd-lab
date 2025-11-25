from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.routers import travel_plans, locations
from app.config import settings
# Імпортуємо schemas, щоб forward references вирішились
from app.schemas import travel_plan, location

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API для управління планами подорожей та локаціями",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Перетворює 422 на 400 для сумісності з тестами"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Validation error", "detail": str(exc)}
    )

# Підключення роутерів (формат згідно з тестами)
app.include_router(travel_plans.router, prefix="/api/travel-plans", tags=["travel-plans"])
app.include_router(locations.router, prefix="/api/locations", tags=["locations"])


@app.get("/")
async def root():
    return {
        "message": "Ласкаво просимо до FastAPI проекту!",
        "docs": "/docs",
        "version": settings.VERSION
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

