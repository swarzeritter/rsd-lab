from pydantic import BaseModel, Field, model_validator, field_validator, model_serializer
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Назва локації")
    address: Optional[str] = Field(None, description="Адреса локації")
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90, description="Широта")
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180, description="Довгота")
    visit_order: Optional[int] = Field(None, gt=0, description="Порядок відвідування (автоматично призначається, якщо не вказано)")
    arrival_date: Optional[datetime] = Field(None, description="Дата прибуття")
    departure_date: Optional[datetime] = Field(None, description="Дата від'їзду")
    budget: Optional[float] = Field(None, ge=0, description="Бюджет для цієї локації")
    notes: Optional[str] = Field(None, description="Нотатки")

    @model_validator(mode='after')
    def validate_dates(self):
        if self.departure_date and self.arrival_date:
            if self.departure_date < self.arrival_date:
                raise ValueError('departure_date повинна бути пізніше або дорівнювати arrival_date')
        return self


class LocationCreate(LocationBase):
    travel_plan_id: Optional[UUID] = Field(None, description="ID плану подорожі (опціонально, якщо створюється через /travel-plans/{id}/locations)")


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    address: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    visit_order: Optional[int] = Field(None, gt=0)
    arrival_date: Optional[datetime] = None
    departure_date: Optional[datetime] = None
    budget: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

    @model_validator(mode='after')
    def validate_dates(self):
        if self.departure_date and self.arrival_date:
            if self.departure_date < self.arrival_date:
                raise ValueError('departure_date повинна бути пізніше або дорівнювати arrival_date')
        return self
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v and (not v.strip()):
            raise ValueError('name cannot be empty or whitespace only')
        return v.strip() if v else v


class LocationResponse(LocationBase):
    id: UUID
    travel_plan_id: UUID
    created_at: datetime

    @model_serializer
    def ser_model(self):
        data = dict(self)
        if 'latitude' in data and data['latitude'] is not None:
            data['latitude'] = float(data['latitude'])
        if 'longitude' in data and data['longitude'] is not None:
            data['longitude'] = float(data['longitude'])
        return data

    class Config:
        from_attributes = True

