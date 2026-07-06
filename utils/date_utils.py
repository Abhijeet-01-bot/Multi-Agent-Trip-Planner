from datetime import datetime
from typing import Optional


def parse_iso_date(date_text: Optional[str]) -> Optional[datetime]:
    """
    Parses an ISO date string in YYYY-MM-DD format.
    Returns datetime object if valid, otherwise None.
    """

    if not date_text:
        return None

    try:
        return datetime.strptime(date_text, "%Y-%m-%d")
    except ValueError:
        return None


def calculate_duration_days(start_date: Optional[str], end_date: Optional[str]) -> Optional[int]:
    """
    Calculates trip duration in days using start_date and end_date.

    Example:
    start_date = 2026-07-10
    end_date = 2026-07-14

    Duration = 5 days because both start and end dates are included.
    """

    start = parse_iso_date(start_date)
    end = parse_iso_date(end_date)

    if not start or not end:
        return None

    if end < start:
        return None

    return (end - start).days + 1


def extract_month_name(start_date: Optional[str]) -> Optional[str]:
    """
    Extracts month name from start date.

    Example:
    2026-07-10 -> July
    """

    start = parse_iso_date(start_date)

    if not start:
        return None

    return start.strftime("%B")