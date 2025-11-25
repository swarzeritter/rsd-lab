from pydantic import BaseModel, Field, field_validator, model_validator, model_serializer
from typing import Optional, TYPE_CHECKING, Any
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal, ROUND_DOWN

if TYPE_CHECKING:
    from app.schemas.location import LocationResponse


class TravelPlanBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Назва плану подорожі")
    description: Optional[str] = Field(None, description="Опис плану подорожі")
    start_date: Optional[date] = Field(None, description="Дата початку подорожі")
    end_date: Optional[date] = Field(None, description="Дата закінчення подорожі")
    budget: Optional[Decimal] = Field(None, ge=0, description="Бюджет подорожі")
    currency: str = Field("USD", min_length=3, max_length=3, description="Валюта")
    is_public: bool = Field(False, description="Чи є план публічним")

    @model_validator(mode='after')
    def validate_dates(self):
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValueError('end_date повинна бути пізніше або дорівнювати start_date')
        return self

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if len(v) != 3:
            raise ValueError('currency повинна містити рівно 3 символи')
        if v != v.upper():
            raise ValueError('currency must be uppercase')
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v or not v.strip():
            raise ValueError('title cannot be empty or whitespace only')
        return v.strip()
    
    @field_validator('budget')
    @classmethod
    def validate_budget(cls, v):
        if v is not None:
            # Перевіряємо, що budget має максимум 2 десяткові знаки
            v_str = str(v)
            if '.' in v_str:
                decimal_part = v_str.split('.')[1]
                if len(decimal_part) > 2:
                    raise ValueError('budget must have at most 2 decimal places')
            v = Decimal(v_str)
        return v


class TravelPlanCreate(TravelPlanBase):
    pass


class TravelPlanUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    is_public: Optional[bool] = None
    version: Optional[int] = Field(None, gt=0)

    @model_validator(mode='after')
    def validate_dates(self):
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValueError('end_date повинна бути пізніше або дорівнювати start_date')
        return self

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        if v and len(v) != 3:
            raise ValueError('currency повинна містити рівно 3 символи')
        return v.upper() if v else v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if v and (not v.strip()):
            raise ValueError('title cannot be empty or whitespace only')
        return v.strip() if v else v
    
    @field_validator('budget')
    @classmethod
    def validate_budget(cls, v):
        if v is not None:
            # Перевіряємо, що budget має максимум 2 десяткові знаки
            v_str = str(v)
            if '.' in v_str:
                decimal_part = v_str.split('.')[1]
                if len(decimal_part) > 2:
                    raise ValueError('budget must have at most 2 decimal places')
            v = Decimal(v_str)
        return v


class TravelPlanResponse(TravelPlanBase):
    id: UUID
    version: int
    created_at: datetime
    updated_at: datetime

    @model_serializer
    def ser_model(self):
        data = dict(self)
        if 'budget' in data and data['budget'] is not None:
            data['budget'] = float(data['budget'])
        return data

    class Config:
        from_attributes = True


class TravelPlanWithLocations(TravelPlanResponse):
    # Використовуємо forward reference для уникнення циклічного імпорту
    locations: list["LocationResponse"] = Field(default_factory=list)

    class Config:
        from_attributes = True

