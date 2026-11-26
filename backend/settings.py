"""App-wide settings for Kanban Lite, read from environment variables."""

import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

# The bakery's time zone, from the BAKERY_TIMEZONE environment variable.
# 'Today', business dates and review deadlines use it; times are stored in UTC.
BAKERY_TIMEZONE = ZoneInfo(os.environ.get("BAKERY_TIMEZONE", "America/New_York"))


def bakery_today() -> date:
    """Today's date at the bakery (not in UTC)."""
    return datetime.now(BAKERY_TIMEZONE).date()


# Web addresses allowed to call the API from a browser (CORS).
# Several addresses can be listed, separated by commas.
FRONTEND_ORIGINS = os.environ.get("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
