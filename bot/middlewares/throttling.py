from aiogram import BaseMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
import logging

from db.database import Database

from settings import config

from cachetools import TTLCache

from utils.phrases import ErrorPhrases

log = logging.getLogger(__name__)


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, session: async_sessionmaker[AsyncSession], ttl: int = 5):
        self.config = config
        self.session = session
        self.ttl = ttl
        self.user_timeouts = TTLCache(maxsize=10000, ttl=ttl)
        self.notified_users = TTLCache(maxsize=10000, ttl=ttl)
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
            if user in self.config.admins:
                return await handler(event, data)

            # Check if user is registered (for all other commands)
            # registered_user = await db.get_user(event.from_user.id)
            # if not registered_user:
            #     if hasattr(event, "answer"):
            #         await event.answer(Phrases.registration_required())
            #     elif hasattr(event, "message"):
            #         await event.answer(Phrases.registration_required(), show_alert=True)
            #     return

            # Throttling logic
            if user in self.user_timeouts:
                if user not in self.notified_users:
                    # For messages
                    if hasattr(event, "answer"):
                        await event.answer(ErrorPhrases.flood_warning(self.ttl))
                    # For callback queries
                    elif hasattr(event, "message") and hasattr(event.message, "answer"):
                        await event.message.answer(ErrorPhrases.flood_warning(self.ttl))

                    self.notified_users[user] = None

                return None

            self.user_timeouts[user] = None

            return await handler(event, data)
