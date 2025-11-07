from datetime import datetime


def get_unix_now() -> int:
    """Get UNIX timestamp"""

    return datetime.now().timestamp()


def utc_to_unix(date: str):
    """Convert UTC to UNIX, UTC is format YYYY-MM-DD HH:MM:SS"""

    return datetime.strptime(date, "%Y-%m-%d %H:%M:%S").timestamp()


def unix_to_utc(timestamp: int):
    """Convert UNIX to UTC, format YYYY-MM-DD HH:MM:SS"""

    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
