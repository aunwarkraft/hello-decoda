from sqlalchemy import Column, String, DateTime, Boolean, Text, UniqueConstraint, Index
from sqlalchemy.sql import func
from database import Base
from datetime import datetime


class ProviderDB(Base):
    __tablename__ = "providers"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class AppointmentDB(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        # Unique constraint to prevent double-booking
        UniqueConstraint('provider_id', 'start_time',
                         name='uq_provider_start_time'),
        # Explicit indexes
        Index('idx_provider_id', 'provider_id'),
        Index('idx_start_time', 'start_time'),
    )

    id = Column(String, primary_key=True, index=True)
    reference_number = Column(String, unique=True, nullable=False, index=True)
    slot_id = Column(String, nullable=False, index=True)
    provider_id = Column(String, nullable=False, index=True)
    patient_first_name = Column(String, nullable=False)
    patient_last_name = Column(String, nullable=False)
    patient_email = Column(String, nullable=False)
    patient_phone = Column(String, nullable=False)
    reason = Column(Text, nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    status = Column(String, default="confirmed", nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
