import asyncio
import logging

from aiogram import BaseMiddleware

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from config import Settings

from cachetools import TTLCache

from bot.db.database import Database
from bot.utils.phrases import ErrorPhrases

log = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, session: async_sessionmaker[AsyncSession], config: Settings):
        self.config = config
        self.session = session
        self.ttl = config.bot.ttl_default
        self.user_timeouts = TTLCache(maxsize=10000, ttl=config.bot.ttl_default)
        self.notified_users = TTLCache(maxsize=10000, ttl=config.bot.ttl_default)

        self._cache_lock = asyncio.Lock()
        super().__init__()

    async def __call__(self, handler, event, data):
        event_user = data.get("event_from_user")

        if not event_user:
            return await handler(event, data)

        user = event_user.id

        async with self.session() as session:
            db = Database(session=session)
            data["db"] = db

            # попуск админов
            if user in self.config.bot.admins:
                return await handler(event, data)

            # Throttling logic
            # async with self._cache_lock:
            #     if user in self.user_timeouts:
            #         if user not in self.notified_users:
            #             # For messages
            #             if hasattr(event, "answer"):
            #                 await event.answer(ErrorPhrases.flood_warning(self.ttl))
            #             # For callback queries
            #             elif hasattr(event, "message") and hasattr(
            #                 event.message, "answer"
            #             ):
            #                 await event.message.answer(
            #                     ErrorPhrases.flood_warning(self.ttl)
            #                 )

            #             self.notified_users[user] = None

            #         return None

            #     self.user_timeouts[user] = None

            # Refactor to move I/O operations outside the lock:
            # # Throttling logic
            should_notify = False
            should_throttle = False

            async with self._cache_lock:
                if user in self.user_timeouts:
                    should_throttle = True

                    if user not in self.notified_users:
                        should_notify = True
                        self.notified_users[user] = None
                else:
                    self.user_timeouts[user] = None

            if should_throttle:
                if should_notify:
                    # For messages
                    if hasattr(event, "answer"):
                        await event.answer(ErrorPhrases.flood_warning(self.ttl))

                    # For callback queries
                    elif hasattr(event, "message") and hasattr(event.message, "answer"):
                        await event.message.answer(ErrorPhrases.flood_warning(self.ttl))

                return None

            return await handler(event, data)
