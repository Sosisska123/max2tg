import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db.database import Database

from bot.keyboards.user_kb import reply_startup_kb
from bot.keyboards.setup_ui import set_bot_commands

from bot.utils.phrases import ErrorPhrases, Phrases

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_command(message: Message, db: Database) -> None:
    try:
        if await db.get_user(message.from_user.id):
            await message.answer(Phrases.already_registered())
            return

        await db.create_user(message.from_user.id, message.from_user.username)

        await message.answer(Phrases.success(), reply_markup=reply_startup_kb())
        logger.info("User %s registered", message.from_user.username)
        await set_bot_commands(message.bot)

    except Exception as e:
        await message.reply(ErrorPhrases.something_went_wrong())
        logger.error(e)
