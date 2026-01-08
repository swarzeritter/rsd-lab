# from sqlalchemy import Column, String, Text, Numeric, Integer, DateTime, ForeignKey, CheckConstraint, Index
# from sqlalchemy.dialects.postgresql import UUID
# from sqlalchemy.sql import func
# from sqlalchemy.orm import relationship
# import uuid
# from app.database import Base


# class Location(Base):
#     __tablename__ = "locations"
#
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
#     travel_plan_id = Column(UUID(as_uuid=True), ForeignKey('travel_plans.id', ondelete='CASCADE'), nullable=False)
#     name = Column(String(200), nullable=False)
#     address = Column(Text, nullable=True)
#     latitude = Column(Numeric(10, 6), nullable=True)
#     longitude = Column(Numeric(11, 6), nullable=True)
#     visit_order = Column(Integer, nullable=False)
#     arrival_date = Column(DateTime(timezone=True), nullable=True)
#     departure_date = Column(DateTime(timezone=True), nullable=True)
#     budget = Column(Numeric(10, 2), nullable=True)
#     notes = Column(Text, nullable=True)
#     created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
#
#     # Зв'язок з travel_plan
#     travel_plan = relationship("TravelPlan", back_populates="locations")
#
#     # Constraints та індекси
#     __table_args__ = (
#         CheckConstraint('length(name) > 0', name='location_name_length_check'),
#         CheckConstraint('latitude >= -90 AND latitude <= 90', name='location_latitude_check'),
#         CheckConstraint('longitude >= -180 AND longitude <= 180', name='location_longitude_check'),
#         CheckConstraint('visit_order > 0', name='location_visit_order_check'),
#         CheckConstraint('budget >= 0', name='location_budget_check'),
#         CheckConstraint('departure_date >= arrival_date', name='check_location_dates'),
#         Index('idx_locations_travel_plan_id', 'travel_plan_id'),
#     )

# MIGRATION NOTE: Цей клас застарів. Локації тепер зберігаються як JSONB в TravelPlan.locations
class Location:
    pass
