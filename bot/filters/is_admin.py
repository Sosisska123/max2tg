from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from config import config


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message | CallbackQuery) -> bool:
        return message.from_user.id in config.bot.admins
