from datetime import datetime, timedelta
import pytz
from config import settings

# Get timezone
TZ = pytz.timezone(settings.TIMEZONE)


def get_local_now() -> datetime:
    """Get current time in practice timezone"""
    return datetime.now(TZ)


def to_utc(dt: datetime) -> datetime:
    """Convert local datetime to UTC"""
    if dt.tzinfo is None:
        dt = TZ.localize(dt)
    return dt.astimezone(pytz.UTC)


def from_utc(dt: datetime) -> datetime:
    """Convert UTC datetime to local timezone"""
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(TZ)


def format_iso8601(dt: datetime) -> str:
    """Format datetime as ISO8601 with timezone"""
    if dt.tzinfo is None:
        dt = TZ.localize(dt)
    return dt.isoformat()
