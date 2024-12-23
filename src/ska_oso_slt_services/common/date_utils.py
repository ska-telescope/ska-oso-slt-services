import logging
from datetime import datetime
from os import getenv
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


def set_telescope_type(env_variable: str) -> str:
    """
    Returns the current date and time for the specified timezone.

    Args:
        env_variable (str): A env variable e.g. - TELESCOPE_TYPE

    Returns:
        datetime: A datetime object representing
        the current time in the specified timezone
    """

    TELESCOPE_TYPE = getenv(env_variable)

    if TELESCOPE_TYPE is None:
        return "mid"
    if "mid" in TELESCOPE_TYPE.lower():
        return "mid"
    if "low" in TELESCOPE_TYPE.lower():
        return "low"
