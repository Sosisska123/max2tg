import datetime
from typing import Optional

from db.database import Database
from models.schedule import Schedule, ScheduleType
from utils.date_utils import get_tomorrow_date


async def get_schedule(
    db: Database, group: str, date: datetime.date
) -> Optional[Schedule]:
    """Get schedule for a date shortcut

    Args:
        db (Database): Bot database
        group (str): User group
        date (datetime.date): Date of the schedule


    Returns:
        Optional[Schedule]: The new schedule object
    """
    return await db.get_schedule(group, date)


async def get_tomorrow_schedule(db: Database, group: str) -> Optional[Schedule]:
    """Get tomorrow schedule shortcut

    Args:
        db (Database): Bot database
        group (str): User group

    Returns:
        Optional[Schedule]: The new schedule object
    """
    return await db.get_tomorrow_schedule(group)


async def get_today_schedule(db: Database, group: str) -> Optional[Schedule]:
    """Get today schedule shortcut

    Args:
        db (Database): Bot database
        group (str): User group

    Returns:
        Optional[Schedule]: The new schedule object
    """
    return await db.get_today_schedule(group)


async def get_default_ring_schedule(db: Database, group: str) -> Optional[Schedule]:
    """Get default ring schedule shortcut. The general schedule for daily


    Args:
        db (Database): Bot database
        group (str): User group

    Returns:
        Optional[Schedule]: The new schedule object
    """
    return await db.get_ring_schedule(group, ScheduleType.DEFAULT_RING.value)


async def get_ring_schedule(db: Database, group: str) -> list[Optional[Schedule], str]:
    """Get new schedule if it exists. Otherwise it returns default ring schedule


    Args:
        db (Database): Bot database
        group (str): User group

    Returns:
        list[Optional[Schedule], str]: List of the new ring schedule object and its type
    """
    ring_type = ScheduleType.RING.value
    schedule = await db.get_ring_schedule(group, ScheduleType.RING.value)

    if not schedule:
        schedule = await db.get_ring_schedule(group, ScheduleType.DEFAULT_RING.value)
        ring_type = ScheduleType.DEFAULT_RING.value

    return schedule, ring_type


async def save_schedule(
    db: Database,
    group: str,
    date: str,
    url: str,
    file_type: str,
) -> Optional[Schedule]:
    """Update a schedule. Create the new if it doesn't exist

    Args:
        db (Database): Bot database
        group (str): User group
        date (str): Schedule date
        url (str): Schedule URL (VK)
        file_type (str): File type [photo/doc]


    Returns:
        Optional[Schedule]: The new schedule object
    """
    if await db.get_schedule(group, date):
        return await db.update_schedule(group, date, url)

    return await db.save_schedule(
        group, date, url, file_type, ScheduleType.REGULAR.value
    )


async def save_ring_schedule(
    db: Database,
    group: str,
    date: str,
    url: str,
    type: ScheduleType = ScheduleType.RING.value,
) -> Optional[Schedule]:
    """Update a ring schedule. Create the new if it doesn't exist

    Args:
        db (Database): Bot database
        group (str): User group
        date (str): Schedule date
        url (str): Schedule URL (VK)
        type (str): Ring type [default/ring]


    Returns:
        Optional[Schedule]: The new schedule object
    """
    return await db.save_ring_schedule(group, date, url, type)


async def update_today_schedule(
    db: Database, group: str, url: str
) -> Optional[Schedule]:
    return await db.update_today_schedule(group, url)


async def update_tomorrow_schedule(
    db: Database, group: str, url: str
) -> Optional[Schedule]:
    """Manually update tomorrow schedule

    Args:
        db (Database): Bot database
        group (str): User group
        url (str): New schedule URL


    Returns:
        Optional[Schedule]: The new schedule object
    """
    return await db.update_schedule(group, url, get_tomorrow_date())


async def update_ring_schedule(
    db: Database, group: str, url: str
) -> Optional[Schedule]:
    """Update today ring schedule

    Args:
        db (Database): Bot database
        group (str): User group
        url (str): New schedule URL


    Returns:
        Optional[Schedule]: The new schedule object
    """
    return await db.update_ring_schedule(group, url)


async def update_default_ring_schedule(
    db: Database,
    group: str,
    url: str,
) -> Optional[Schedule]:
    """Update default ring schedule

    Args:
        db (Database): Bot database
        group (str): User group
        url (str): New schedule URL


    Returns:
        Optional[Schedule]: The new schedule object
    """
    return await db.update_ring_schedule(group, url, ScheduleType.DEFAULT_RING.value)
