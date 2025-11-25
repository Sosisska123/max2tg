import logging
from typing import Optional, List

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from max.models.max_account import Base, MaxAccount


log = logging.getLogger(__name__)


async def init_max_db(engine):
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


class MaxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_account(
        self, user_tg_id: int, listening_chat_id: int, token: str
    ) -> Optional[MaxAccount]:
        """Add new account if it doesn't exist. Returns the new user object"""
        try:
            account = MaxAccount(
                user_tg_id=user_tg_id,
                target_chat_id=listening_chat_id,
                token=token,
            )

            self.session.add(account)
            await self.session.commit()
            return account
        except SQLAlchemyError as e:
            log.error(f"Error saving account {user_tg_id}: {e}")
            await self.session.rollback()
            return None

    async def get_account(self, user_tg_id: int) -> Optional[MaxAccount]:
        """Get user by Telegram ID"""

        try:
            result = await self.session.execute(
                select(MaxAccount).where(MaxAccount.user_tg_id == user_tg_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error(f"Error getting account {user_tg_id}: {e}")
            return None

    async def get_all_accounts(self) -> List[MaxAccount]:
        """Get all users from a certain group"""

        try:
            stmt = select(MaxAccount)

            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            log.error(f"Error getting MAX accounts: {e}")
            return []

    async def update_listening_chat(
        self, user_tg_id: int, target_chat_id: Optional[int]
    ):
        """Messages will forward from a certain chat instead of resending any incoming message"""

        try:
            stmt = (
                update(MaxAccount)
                .where(MaxAccount.user_tg_id == user_tg_id)
                .values(target_chat_id=target_chat_id)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            log.error(f"Error updating listening chat for user {user_tg_id}: {e}")
            await self.session.rollback()
            return False
