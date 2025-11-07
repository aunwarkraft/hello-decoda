from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from db_models import ProviderDB, AppointmentDB
from config import settings
import pytz
from utils import format_iso8601

TZ = pytz.timezone(settings.TIMEZONE)


def get_db_session() -> Session:
    """Get database session"""
    return SessionLocal()


def get_providers() -> list[Dict[str, Any]]:
    """
    Get all providers from the database.
    """
    db = get_db_session()
    try:
        providers = db.query(ProviderDB).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "specialty": p.specialty,
                "bio": p.bio
            }
            for p in providers
        ]
    finally:
        db.close()


def get_provider_by_id(provider_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single provider by ID.
    """
    db = get_db_session()
    try:
        provider = db.query(ProviderDB).filter(
            ProviderDB.id == provider_id).first()
        if provider:
            return {
                "id": provider.id,
                "name": provider.name,
                "specialty": provider.specialty,
                "bio": provider.bio
            }
        return None
    finally:
        db.close()


def check_slot_availability(slot_id: str, provider_id: str) -> bool:
    """
    Check if a time slot is available for booking.
    """
    db = get_db_session()
    try:
        existing = db.query(AppointmentDB).filter(
            AppointmentDB.slot_id == slot_id,
            AppointmentDB.provider_id == provider_id,
            AppointmentDB.status == "confirmed"
        ).first()
        return existing is None
    finally:
        db.close()


def create_appointment(appointment_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new appointment in the database.
    Stores datetimes in UTC, returns in local timezone for API response.
    """
    db = get_db_session()
    try:
        # Parse datetime strings - they come in as UTC ISO8601 strings
        # Handle both "Z" suffix and "+00:00" format
        start_time_str = appointment_data["start_time"].replace("Z", "+00:00")
        end_time_str = appointment_data["end_time"].replace("Z", "+00:00")
        created_at_str = appointment_data["created_at"].replace("Z", "+00:00")

        # Parse as UTC datetimes
        start_time = datetime.fromisoformat(start_time_str)
        if start_time.tzinfo is None:
            start_time = pytz.UTC.localize(start_time)
        else:
            start_time = start_time.astimezone(pytz.UTC)

        end_time = datetime.fromisoformat(end_time_str)
        if end_time.tzinfo is None:
            end_time = pytz.UTC.localize(end_time)
        else:
            end_time = end_time.astimezone(pytz.UTC)

        created_at = datetime.fromisoformat(created_at_str)
        if created_at.tzinfo is None:
            created_at = pytz.UTC.localize(created_at)
        else:
            created_at = created_at.astimezone(pytz.UTC)

        appointment = AppointmentDB(
            id=appointment_data["id"],
            reference_number=appointment_data["reference_number"],
            slot_id=appointment_data["slot_id"],
            provider_id=appointment_data["provider_id"],
            patient_first_name=appointment_data["patient_first_name"],
            patient_last_name=appointment_data["patient_last_name"],
            patient_email=appointment_data["patient_email"],
            patient_phone=appointment_data["patient_phone"],
            reason=appointment_data["reason"],
            # Store as naive UTC (SQLite compatibility)
            start_time=start_time.replace(tzinfo=None),
            end_time=end_time.replace(tzinfo=None),
            status=appointment_data["status"],
            created_at=created_at.replace(tzinfo=None)
        )

        db.add(appointment)
        db.commit()
        db.refresh(appointment)

        # Return in the format expected by the API
        # Convert from naive UTC (stored) to local timezone for display
        start_time_utc = pytz.UTC.localize(appointment.start_time)
        end_time_utc = pytz.UTC.localize(appointment.end_time)
        created_at_utc = pytz.UTC.localize(appointment.created_at)

        start_time_local = start_time_utc.astimezone(TZ)
        end_time_local = end_time_utc.astimezone(TZ)
        created_at_local = created_at_utc.astimezone(TZ)

        return {
            "id": appointment.id,
            "reference_number": appointment.reference_number,
            "slot_id": appointment.slot_id,
            "provider_id": appointment.provider_id,
            "patient_first_name": appointment.patient_first_name,
            "patient_last_name": appointment.patient_last_name,
            "patient_email": appointment.patient_email,
            "patient_phone": appointment.patient_phone,
            "reason": appointment.reason,
            # Return as ISO8601 with timezone offset
            "start_time": format_iso8601(start_time_local),
            "end_time": format_iso8601(end_time_local),
            "status": appointment.status,
            "created_at": format_iso8601(created_at_local)
        }
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


def get_booked_slots(provider_id: str, start_date: str, end_date: str) -> set[str]:
    """
    Get all booked slot IDs for a provider within a date range.
    """
    db = get_db_session()
    try:
        # Parse dates in local timezone
        start = TZ.localize(datetime.strptime(start_date, "%Y-%m-%d"))
        end = TZ.localize(datetime.strptime(end_date, "%Y-%m-%d")
                          ).replace(hour=23, minute=59, second=59)

        # Convert to UTC for database query (database stores in UTC)
        start_utc = start.astimezone(pytz.UTC)
        end_utc = end.astimezone(pytz.UTC)
        # Convert to naive UTC for SQLite comparison (SQLite doesn't handle timezone-aware datetimes well)
        # SQLAlchemy with SQLite will return naive datetimes, so we compare naive UTC
        start_utc_naive = start_utc.replace(tzinfo=None)
        end_utc_naive = end_utc.replace(tzinfo=None)

        appointments = db.query(AppointmentDB).filter(
            AppointmentDB.provider_id == provider_id,
            AppointmentDB.start_time >= start_utc_naive,
            AppointmentDB.start_time <= end_utc_naive,
            AppointmentDB.status == "confirmed"
        ).all()

        return {apt.slot_id for apt in appointments}
    finally:
        db.close()


def get_provider_appointments(provider_id: str, start_date: str, end_date: str) -> list[Dict[str, Any]]:
    """
    Get all appointments for a provider within a date range.
    """
    db = get_db_session()
    try:
        # Parse dates in local timezone
        start = TZ.localize(datetime.strptime(start_date, "%Y-%m-%d"))
        end = TZ.localize(datetime.strptime(end_date, "%Y-%m-%d")
                          ).replace(hour=23, minute=59, second=59)

        # Convert to UTC for database query
        start_utc = start.astimezone(pytz.UTC)
        end_utc = end.astimezone(pytz.UTC)

        # Convert to naive UTC for SQLite comparison
        start_utc_naive = start_utc.replace(tzinfo=None)
        end_utc_naive = end_utc.replace(tzinfo=None)

        appointments = db.query(AppointmentDB).filter(
            AppointmentDB.provider_id == provider_id,
            AppointmentDB.start_time >= start_utc_naive,
            AppointmentDB.start_time <= end_utc_naive
        ).all()

        return [
            {
                "id": apt.id,
                "patient_name": f"{apt.patient_first_name} {apt.patient_last_name}",
                "patient_email": apt.patient_email,
                # Convert from naive UTC (stored) to local timezone for display
                "start_time": format_iso8601(pytz.UTC.localize(apt.start_time).astimezone(TZ)),
                "end_time": format_iso8601(pytz.UTC.localize(apt.end_time).astimezone(TZ)),
                "reason": apt.reason,
                "status": apt.status
            }
            for apt in appointments
        ]
    finally:
        db.close()
