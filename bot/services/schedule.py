from typing import Optional

from db.database import Database
from models.schedule import Schedule, ScheduleType


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
