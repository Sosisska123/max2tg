import logging

from typing import Optional, List

from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from max.models.max_account import MaxBase, MaxAccount
from max.models.groups import Chat, Group


log = logging.getLogger(__name__)


async def init_max_db(engine):
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(MaxBase.metadata.create_all)


class MaxRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_account(self, user_tg_id: int, token: str) -> Optional[MaxAccount]:
        """Add new account if it doesn't exist. Returns the new user object"""
        try:
            account = MaxAccount(
                tg_id=user_tg_id,
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
                select(MaxAccount).where(MaxAccount.tg_id == user_tg_id)
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

    async def set_user_token(self, user_tg_id: int, token: str) -> bool:
        """Set user token"""
        try:
            stmt = (
                update(MaxAccount)
                .where(MaxAccount.tg_id == user_tg_id)
                .values(token=token)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            log.error(f"Error updating token for user {user_tg_id}: {e}")
            await self.session.rollback()
            return False

    async def get_user_token(self, user_tg_id: int) -> Optional[str]:
        """Get user token"""
        try:
            result = await self.session.execute(
                select(MaxAccount.token).where(MaxAccount.tg_id == user_tg_id)
            )
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error(f"Error getting user {user_tg_id}: {e}")
            return None

    # ---

    async def add_group(
        self, owner_id: int, group_title: str, group_id: int, chat_id: int = None
    ) -> bool:
        try:
            stmt = (
                insert(Group)
                .values(
                    user_tg_id=owner_id,
                    group_title=group_title,
                    group_id=group_id,
                    connected_chat_id=chat_id,
                )
                .on_conflict_do_nothing()
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            log.error(f"Error saving group {group_id}: {e}")
            await self.session.rollback()
            return None

    async def save_or_update_user_chat(
        self,
        owner_id: int,
        chat_id: int,
        chat_title: str,
        messages_count: int = None,
        last_message_id: int = None,
    ) -> bool:
        try:
            stmt = (
                insert(Chat)
                .values(
                    user_tg_id=owner_id,
                    chat_id=chat_id,
                    chat_title=chat_title,
                    messages_count=messages_count,
                    last_message_id=last_message_id,
                )
                .on_conflict_do_update(
                    index_elements=["user_tg_id"],
                    set_=dict(
                        chat_id=chat_id,
                        chat_title=chat_title,
                        messages_count=messages_count,
                        last_message_id=last_message_id,
                    ),
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            log.error(f"Error updating chat {chat_id}: {e}")
            await self.session.rollback()
            return False

    async def connect_group_to_chat(self, group_id: int, chat_id: int) -> bool:
        try:
            stmt = (
                update(Group)
                .where(Group.group_id == group_id)
                .values(connected_chat_id=chat_id)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            log.error(f"Error connecting group {group_id} to chat {chat_id}: {e}")
            await self.session.rollback()
            return False

    async def remove_tg_group(self, group_id: int) -> bool:
        try:
            stmt = (
                update(Group)
                .where(Group.group_id == group_id)
                .values(connected_chat_id=None)
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            log.error(f"Error removing group {group_id}: {e}")
            await self.session.rollback()
            return False

    async def get_subscribed_tg_groups(self, chat_id) -> Optional[list[Group]]:
        """Get all TG Groups subscribed to the MAX chat"""

        try:
            stmt = select(Group).where(Group.connected_chat_id == chat_id)

            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            log.error(f"Error getting subscribed TG Groups: {e}")
            return []

    async def get_group(self, group_id) -> Group:
        try:
            stmt = select(Group).where(Group.group_id == group_id)

            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            log.error(f"Error getting TG Group: {e}")
            return None

    async def get_max_available_chats(self, owner_id: int) -> Optional[list[Chat]]:
        try:
            stmt = select(Chat).where(Chat.user_tg_id == owner_id)

            result = await self.session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            log.error(f"Error getting MAX chats for user: {e}")
            return []
