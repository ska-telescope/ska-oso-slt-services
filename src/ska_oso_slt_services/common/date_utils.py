import logging
from datetime import datetime
from zoneinfo import ZoneInfo

LOGGER = logging.getLogger(__name__)


def get_datetime_for_timezone(timezone_str: str) -> datetime:
    """
    Returns the current date and time for the specified timezone.

    Args:
        timezone_str (str): A string representing
        the desired timezone (e.g., 'UTC', 'America/New_York', 'Europe/London')

    Returns:
        datetime: A datetime object representing
        the current time in the specified timezone
    """
    try:
        tz = ZoneInfo(timezone_str)
        return datetime.now(tz)
    except Exception as e:  # pylint: disable=W0718
        LOGGER.info("Unexpected error: %s", e)
        return datetime.now(ZoneInfo("UTC"))
