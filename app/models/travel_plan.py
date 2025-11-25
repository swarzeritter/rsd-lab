from sqlalchemy import Column, String, Text, Date, Numeric, Boolean, Integer, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class TravelPlan(Base):
    __tablename__ = "travel_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    budget = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), nullable=False, server_default='USD')
    is_public = Column(Boolean, nullable=False, server_default='false')
    version = Column(Integer, nullable=False, server_default='1')
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Зв'язок з локаціями
    locations = relationship("Location", back_populates="travel_plan", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint('length(title) > 0', name='travel_plan_title_length_check'),
        CheckConstraint('length(currency) = 3', name='travel_plan_currency_length_check'),
        CheckConstraint('budget >= 0', name='travel_plan_budget_check'),
        CheckConstraint('version > 0', name='travel_plan_version_check'),
        CheckConstraint('end_date >= start_date', name='check_plan_dates'),
    )

