from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import random
import pytz

from models import (
    Provider,
    TimeSlot,
    CreateAppointmentRequest,
    Appointment,
    AvailabilityResponse,
    AppointmentSlot,
    AppointmentProvider
)
from repository import (
    get_providers,
    get_provider_by_id,
    check_slot_availability,
    create_appointment,
    get_booked_slots,
    get_provider_appointments
)
from config import settings
from utils import (
    get_local_now,
    to_utc,
    from_utc,
    format_iso8601,
    TZ
)
from errors import (
    NotFoundError,
    ValidationError,
    ConflictError,
    UnprocessableEntityError
)
from database import init_db
from db_models import ProviderDB
from database import SessionLocal
import os

app = FastAPI(title="Healthcare Appointment API", version="1.0.0")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database and seed providers if needed"""
    try:
        # Ensure database directory exists (for SQLite)
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        if db_path and db_path != ":memory:":
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
        
        # Create tables
        init_db()
        
        # Seed providers if they don't exist
        db = SessionLocal()
        try:
            if db.query(ProviderDB).count() == 0:
                from __init__db import seed_providers
                seed_providers()
        finally:
            db.close()
    except Exception as e:
        print(f"Warning: Database initialization error: {e}")

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "message": "Healthcare Appointment API",
        "docs": "/docs",
        "endpoints": {
            "providers": "/api/providers",
            "availability": "/api/availability",
            "appointments": "/api/appointments"
        }
    }


@app.get("/api/providers", response_model=list[Provider])
async def list_providers():
    """
    Get all healthcare providers.
    """
    providers = get_providers()
    return providers


@app.get("/api/availability", response_model=AvailabilityResponse)
async def get_availability(
    provider_id: str = Query(..., description="Provider ID"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """
    Get available time slots for a provider within a date range.

    Business Rules:
    - 30-minute slots
    - 9:00 AM - 5:00 PM
    - Skip lunch (12:00 PM - 1:00 PM)
    - Skip weekends
    - Only future slots
    """
    # Validate provider exists
    provider = get_provider_by_id(provider_id)
    if not provider:
        raise NotFoundError("Provider not found")

    # Parse dates in local timezone
    try:
        start = TZ.localize(datetime.strptime(start_date, "%Y-%m-%d"))
        end = TZ.localize(datetime.strptime(end_date, "%Y-%m-%d"))
    except ValueError:
        raise ValidationError("Invalid date format. Use YYYY-MM-DD")

    if end <= start:
        raise ValidationError("end_date must be after start_date")

    # Get booked slots
    booked_slots = get_booked_slots(provider_id, start_date, end_date)

    # Generate time slots in local timezone
    slots = []
    current_date = start
    now = get_local_now()

    while current_date <= end:
        # Skip weekends (0 = Monday, 6 = Sunday)
        if current_date.weekday() < 5:  # Monday to Friday
            # Generate slots from 9 AM to 5 PM
            for hour in range(9, 17):
                for minute in [0, 30]:
                    # Skip lunch hour (12:00 PM - 1:00 PM)
                    if hour == 12:
                        continue

                    # Create slot start time in local timezone
                    # Use replace() which preserves timezone awareness
                    slot_start = current_date.replace(
                        hour=hour, minute=minute, second=0, microsecond=0)
                    # Ensure timezone is preserved
                    if slot_start.tzinfo is None:
                        slot_start = TZ.localize(slot_start)
                    slot_end = slot_start + timedelta(minutes=30)

                    # Only include future slots
                    if slot_start > now:
                        slot_id = f"slot-{provider_id}-{int(slot_start.timestamp() * 1000)}"

                        slots.append(TimeSlot(
                            id=slot_id,
                            start_time=format_iso8601(slot_start),
                            end_time=format_iso8601(slot_end),
                            available=slot_id not in booked_slots
                        ))

        current_date += timedelta(days=1)

    return AvailabilityResponse(
        provider=AppointmentProvider(
            id=provider["id"],
            name=provider["name"],
            specialty=provider["specialty"]
        ),
        slots=slots
    )


@app.post("/api/appointments", response_model=Appointment, status_code=201)
async def book_appointment(request: CreateAppointmentRequest):
    """
    Create a new appointment.

    Validates:
    - Provider exists
    - Slot is available
    - Patient information is valid
    - Reason for visit is provided
    - Slot is in allowed window (not weekend/lunch)
    """
    # Validate provider exists
    provider = get_provider_by_id(request.provider_id)
    if not provider:
        raise NotFoundError("Provider not found")

    # Parse slot ID to get times
    try:
        # Extract timestamp from slot_id: "slot-provider-1-1234567890"
        # The timestamp in slot_id is milliseconds, convert to seconds
        slot_timestamp_ms = int(request.slot_id.split('-')[-1])
        slot_timestamp = slot_timestamp_ms / 1000

        # The timestamp is a POSIX timestamp (UTC-based seconds since epoch)
        # Convert to UTC first, then to local timezone
        # This ensures correct timezone conversion
        start_time_utc = datetime.fromtimestamp(slot_timestamp, tz=pytz.UTC)
        start_time = from_utc(start_time_utc)
        end_time = start_time + timedelta(minutes=30)
    except (ValueError, IndexError) as e:
        raise ValidationError(f"Invalid slot ID format: {str(e)}")

    # Validate slot is in allowed window
    if start_time.weekday() >= 5:  # Weekend
        raise UnprocessableEntityError(
            "Appointments cannot be booked on weekends")
    if start_time.hour == 12:  # Lunch hour
        raise UnprocessableEntityError(
            "Appointments cannot be booked during lunch (12:00-1:00 PM)")
    if start_time.hour < 9 or start_time.hour >= 17:
        raise UnprocessableEntityError(
            "Appointments can only be booked between 9 AM and 5 PM")
    if start_time < get_local_now():
        raise UnprocessableEntityError("Cannot book appointments in the past")

    # Check slot availability
    is_available = check_slot_availability(
        request.slot_id, request.provider_id)
    if not is_available:
        raise ConflictError("This time slot has already been booked", details={
                            "slot_id": request.slot_id})

    # Generate reference number
    date_str = start_time.strftime("%Y%m%d")
    random_num = str(random.randint(0, 999)).zfill(3)
    reference_number = f"REF-{date_str}-{random_num}"

    # Create appointment data
    appointment_data = {
        "id": f"appointment-{int(get_local_now().timestamp() * 1000)}",
        "reference_number": reference_number,
        "slot_id": request.slot_id,
        "provider_id": request.provider_id,
        "patient_first_name": request.patient.first_name,
        "patient_last_name": request.patient.last_name,
        "patient_email": request.patient.email,
        "patient_phone": request.patient.phone,
        "reason": request.reason,
        "start_time": to_utc(start_time).isoformat(),
        "end_time": to_utc(end_time).isoformat(),
        "status": "confirmed",
        "created_at": to_utc(get_local_now()).isoformat()
    }

    # Save appointment
    created = create_appointment(appointment_data)

    # Return formatted response
    return Appointment(
        id=created["id"],
        reference_number=created["reference_number"],
        status=created["status"],
        slot=AppointmentSlot(
            start_time=created["start_time"],
            end_time=created["end_time"]
        ),
        provider=AppointmentProvider(
            id=provider["id"],
            name=provider["name"],
            specialty=provider["specialty"]
        ),
        patient=request.patient,
        reason=created["reason"],
        created_at=created["created_at"]
    )


@app.get("/api/providers/{provider_id}/appointments")
async def get_provider_appointments_endpoint(
    provider_id: str,
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """
    Get all appointments for a provider within a date range.
    """
    provider = get_provider_by_id(provider_id)
    if not provider:
        raise NotFoundError("Provider not found")

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise ValidationError("Invalid date format. Use YYYY-MM-DD")

    if end <= start:
        raise ValidationError("end_date must be after start_date")

    appointments = get_provider_appointments(provider_id, start_date, end_date)

    return {
        "provider_id": provider_id,
        "appointments": appointments
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
