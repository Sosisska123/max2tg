from datetime import datetime, timezone


def get_unix_now() -> int:
    """Get UNIX timestamp"""

    return datetime.now(timezone.utc).timestamp()


def utc_to_unix(date: str) -> int:
    """Convert UTC to UNIX, UTC is format YYYY-MM-DD HH:MM:SS"""

    dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=timezone.utc).timestamp()


def unix_to_utc(timestamp: int) -> str:
    """Convert UNIX to UTC, format YYYY-MM-DD HH:MM:SS"""

    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
