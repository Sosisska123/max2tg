import logging
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import Base, User

log = logging.getLogger(__name__)


async def init_bot_db(engine):
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

    async def update_connection_state(self, user_id: int, conn_state: bool) -> bool:
        """Set user group connection allowed rule"""
        try:
            stmt = (
                update(User)
                .where(User.tg_id == user_id)
                .values(can_connect_max=conn_state)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            log.error(f"Error updating connection state for user {user_id}: {e}")
            await self.session.rollback()
            return False
