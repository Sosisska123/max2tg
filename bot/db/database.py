import datetime
import json
import logging
from typing import List, Optional

from sqlalchemy import delete, desc, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.max_group import Group, MaxGroupConfig
from bot.models.schedule import Schedule, ScheduleType
from bot.models.temp_schedule import TempSchedule
from bot.models.user import Base, User
from bot.utils.date_utils import get_today_date, get_tomorrow_date

log = logging.getLogger(__name__)


async def init_db(engine):
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


class Database:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        try:
            result = await self.session.execute(
                select(User).where(User.tg_id == user_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error(f"Error getting user {user_id}: {e}")
            return None

    async def create_user(
        self, user_id: int, username: str, group: str
    ) -> Optional[User]:
        """Add new user if it doesn't exist. Returns the new user object."""
        try:
            user = User(tg_id=user_id, username=username, group=group)
            self.session.add(user)
            await self.session.commit()
            return user
        except SQLAlchemyError as e:
            log.error(f"Error creating user {user_id}: {e}")
            await self.session.rollback()
            return None

    async def get_notification_state(self, user_id: int) -> Optional[bool]:
        """Get user notification state by Telegram ID."""
        try:
            user = await self.get_user(user_id)
            return user.notification_state if user else None
        except SQLAlchemyError as e:
            log.error(f"Error getting notification state for user {user_id}: {e}")
            return None

    async def update_notification_state(
        self, user_id: int, notification_state: bool
    ) -> bool:
        """Set user notification state by Telegram ID."""
        try:
            stmt = (
                update(User)
                .where(User.tg_id == user_id)
                .values(notification_state=notification_state)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            log.error(f"Error updating notification state for user {user_id}: {e}")
            await self.session.rollback()
            return False

    async def get_all_users_in_group(
        self, group: str, ignore_notification: bool = False
    ) -> List[User]:
        """Get all users from a certain group."""
        try:
            stmt = select(User).where(User.group == group)

            if not ignore_notification:
                stmt = stmt.where(User.notification_state)

            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            log.error(f"Error getting users for group {group}: {e}")
            return []

    # region schedule methods

    async def save_schedule(
        self,
        group: str,
        date: str,
        url: str,
        file_type: str,
        schedule_type: str = ScheduleType.REGULAR.value,
    ) -> Optional[Schedule]:
        """General method for saving schedule."""

        try:
            if file_type not in ("photo", "doc"):
                raise ValueError("file_type must be 'photo' or 'doc'")

            schedule = Schedule(
                group=group,
                url=url,
                date=date,
                schedule_type=schedule_type,
                file_type=file_type,
            )

            self.session.add(schedule)
            await self.session.commit()
            return schedule
        except (SQLAlchemyError, ValueError) as e:
            log.error(f"Error saving schedule for group {group} on {date}: {e}")
            await self.session.rollback()
            return None

    async def get_schedule(self, group: str, date: datetime.date) -> Optional[Schedule]:
        """
        Get schedule for a specific date, prioritizing modified schedules.
        """
        try:
            # Assuming 'modified' > 'regular' alphabetically, so order by desc gives priority.
            stmt = (
                select(Schedule)
                .where(Schedule.group == group, Schedule.date == date)
                .order_by(desc(Schedule.schedule_type))
                .limit(1)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error(f"Error getting schedule for group {group} on {date}: {e}")
            return None

    async def get_tomorrow_schedule(self, group: str) -> Optional[Schedule]:
        """Shortcut for get_schedule(group, get_tomorrow_date())"""
        return await self.get_schedule(group, get_tomorrow_date())

    async def get_today_schedule(self, group: str) -> Optional[Schedule]:
        """Shortcut for get_schedule(group, get_today_date())"""
        return await self.get_schedule(group, get_today_date())

    async def update_schedule(
        self, group: str, date: datetime.date, url: str
    ) -> Optional[Schedule]:
        """Updates `URL` of a schedule, marking it as modified."""
        try:
            stmt = (
                update(Schedule)
                .where(
                    Schedule.group == group,
                    Schedule.date == date,
                    Schedule.schedule_type.in_(
                        [ScheduleType.REGULAR.value, ScheduleType.MODIFIED.value]
                    ),
                )
                .values(url=url, schedule_type=ScheduleType.MODIFIED.value)
            )
            await self.session.execute(stmt)
            await self.session.commit()
            # Return the updated schedule
            return await self.get_schedule(group, date)
        except SQLAlchemyError as e:
            log.error(f"Error updating schedule for group {group} on {date}: {e}")
            await self.session.rollback()
            return None

    # endregion

    # region rings

    async def get_ring_schedule(
        self, group: str, schedule_type: ScheduleType = ScheduleType.DEFAULT_RING
    ) -> Optional[Schedule]:
        """
        Get ring schedule.
        - `RING`: for tomorrow's ring schedule.
        - `DEFAULT_RING`: for the default ring schedule.
        """
        try:
            stmt = select(Schedule).where(
                Schedule.group == group, Schedule.schedule_type == schedule_type.value
            )
            if schedule_type == ScheduleType.RING:
                stmt = stmt.where(Schedule.date == get_tomorrow_date())

            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error(f"Error getting ring schedule for group {group}: {e}")
            return None

    async def save_ring_schedule(
        self,
        group: str,
        url: str,
        schedule_type: ScheduleType,
        date: Optional[datetime.date] = None,
    ) -> Optional[Schedule]:
        """Saves a ring schedule, assuming file_type is 'photo'."""
        if schedule_type == ScheduleType.RING and date is None:
            log.error("Date is required for RING schedule type")
            return None

        return await self.save_schedule(
            group=group,
            date=date.isoformat() if date else None,
            url=url,
            file_type="photo",
            schedule_type=schedule_type.value,
        )

    async def update_ring_schedule(self, group: str, url: str) -> Optional[Schedule]:
        """
        Updates the ring schedule for tomorrow (upsert).
        If a ring schedule for tomorrow exists, it's updated. If not, a new one is created.
        """
        try:
            tomorrow = get_tomorrow_date()
            stmt = select(Schedule).where(
                Schedule.group == group,
                Schedule.date == tomorrow,
                Schedule.schedule_type == ScheduleType.RING.value,
            )
            result = await self.session.execute(stmt)
            schedule = result.scalar_one_or_none()

            if schedule:
                schedule.url = url
                await self.session.commit()
                return schedule
            else:
                return await self.save_ring_schedule(
                    group=group,
                    url=url,
                    date=tomorrow,
                    schedule_type=ScheduleType.RING,
                )
        except SQLAlchemyError as e:
            log.error(f"Error updating ring schedule for group {group}: {e}")
            await self.session.rollback()
            return None

    # endregion

    # region temp schedule
    async def save_temp_schedule(
        self, group: str, file_type: str, files_urls: List[str]
    ) -> Optional[TempSchedule]:
        """
        Saves a temporary schedule. The list of file URLs is stored as a JSON string.
        """
        try:
            temp_schedule = TempSchedule(
                group=group,
                file_type=file_type,
                files_url=json.dumps(files_urls),
            )

            self.session.add(temp_schedule)
            await self.session.commit()

            return temp_schedule
        except SQLAlchemyError as e:
            log.error(f"Error saving temp schedule for group {group}: {e}")
            await self.session.rollback()
            return None

    async def get_temp_schedule(self, temp_id: int) -> Optional[TempSchedule]:
        """
        Gets a temporary schedule. The `files_url` will be a JSON string.
        """
        try:
            result = await self.session.execute(
                select(TempSchedule).where(TempSchedule.id == temp_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error(f"Error getting temp schedule {temp_id}: {e}")
            return None

    async def delete_temp_schedule(self, temp_id: int) -> bool:
        """Deletes a temporary schedule by its ID."""
        try:
            stmt = delete(TempSchedule).where(TempSchedule.id == temp_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            log.error(f"Error deleting temp schedule {temp_id}: {e}")
            await self.session.rollback()
            return False

    async def clear_temp_schedules(self) -> bool:
        """Deletes all temporary schedules."""
        try:
            await self.session.execute(delete(TempSchedule))
            await self.session.commit()

            return True
        except SQLAlchemyError as e:
            log.error(f"Error clearing temp schedules: {e}")
            await self.session.rollback()
            return False

    # endregion

    # region MAX Forwarding Messages

    async def update_user_max_token(self, user_id: int, token: str) -> bool:
        """Set user MAX token"""
        try:
            stmt = (
                update(User).where(User.tg_id == user_id).values(max_short_token=token)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            log.error(f"Error updating MAX state for user {user_id}: {e}")
            await self.session.rollback()
            return False

    async def update_user_max_permission(self, user_id: int, state: bool) -> bool:
        """Defines can user connect MAX"""
        try:
            stmt = (
                update(User).where(User.tg_id == user_id).values(can_connect_max=state)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            log.error(f"Error updating MAX state for user {user_id}: {e}")
            await self.session.rollback()
            return False

    async def connect_tg_max(self, tg_group_id: int, max_chat_id: int) -> bool:
        try:
            group = await self.get_tg_group_by_id(tg_group_id)

            if not group:
                return False

            group.connected_chat_id = max_chat_id

            if group.max_config:
                group.max_config.chat_id = max_chat_id
            else:
                group.max_config = MaxGroupConfig(connected_group_id=max_chat_id)

            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            log.error(
                f"Error connecting Telegram group {tg_group_id} to MAX chat {max_chat_id}: {e}"
            )
            await self.session.rollback()
            return False

    async def disconnect_tg_max(self, tg_group_id: int) -> bool:
        try:
            group = await self.get_tg_group_by_id(tg_group_id)

            if not group:
                return False

            group.connected_chat_id = None
            group.max_config.chat_id = None

            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            log.error(f"Error disconnecting Telegram group {tg_group_id}: {e}")
            await self.session.rollback()
            return False

    async def get_max_token(self, user_id: int) -> Optional[str]:
        """Get user's MAX token."""
        user = await self.get_user(user_id)
        return user.max_short_token if user else None

    async def get_user_max_permission(self, user_id: int) -> bool:
        """Get user's MAX permission."""
        user = await self.get_user(user_id)
        return user.can_connect_max if user else False

    async def store_tg_group(
        self, group_id: int, title: str, creator_id: int
    ) -> Optional[Group]:
        """Save Telegram group to connect MAX to it later"""
        try:
            group = Group(self_id=group_id, group_title=title, creator_id=creator_id)

            self.session.add(group)
            await self.session.commit()
            return group
        except SQLAlchemyError as e:
            log.error(f"Error creating connected group {group_id}: {e}")
            await self.session.rollback()
            return None

    async def remove_tg_group(self, tg_id: int) -> bool:
        """Remove subscribed group."""
        try:
            stmt = delete(Group).where(Group.self_id == tg_id)
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            log.error(f"Error removing connected group {tg_id}: {e}")
            await self.session.rollback()
            return False

    async def get_tg_groups_list(self) -> List[Group]:
        """Get all subscribed group list"""
        try:
            result = await self.session.execute(select(Group))
            return result.scalars().all()
        except SQLAlchemyError as e:
            log.error(f"Error getting connected groups list: {e}")
            return []

    async def get_tg_group_by_id(self, tg_id: int) -> Optional[Group]:
        """Get subscribed group by Telegram ID."""
        try:
            result = await self.session.execute(
                select(Group).where(Group.self_id == tg_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error(f"Error getting connected group {tg_id}: {e}")
            return None

    async def store_user_max_chat(
        self,
        chat_id: int,
        chat_title: str,
        owner_tg_id: int,
        messages_count: int = 0,
        last_message_id: int = 0,
    ) -> Optional[MaxGroupConfig]:
        """Set given chat as listening."""
        try:
            result = await self.session.execute(
                select(MaxGroupConfig).where(
                    MaxGroupConfig.owner_id == owner_tg_id,
                    MaxGroupConfig.chat_id == chat_id,
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.chat_title = chat_title
                existing.last_message_id = last_message_id
                existing.messages_count = messages_count

                await self.session.commit()
                return existing

            else:
                group = MaxGroupConfig(
                    owner_id=owner_tg_id,
                    chat_id=chat_id,
                    chat_title=chat_title,
                    last_message_id=last_message_id,
                    messages_count=messages_count,
                )

                self.session.add(group)
                await self.session.commit()
                return group
        except SQLAlchemyError as e:
            log.error(f"Error creating MAX listening chat {chat_id}: {e}")
            await self.session.rollback()
            return None

    async def get_max_available_chats(self, owner_tg_id: int) -> List[MaxGroupConfig]:
        """Get all added MAX chats for a user"""
        try:
            result = await self.session.execute(
                select(MaxGroupConfig).where(MaxGroupConfig.owner_id == owner_tg_id)
            )

            return result.scalars().all()
        except SQLAlchemyError as e:
            log.error(f"Error getting available MAX chats: {e}")
            return []

    # endregion
