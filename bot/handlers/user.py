import logging
from aiogram import Router
from aiogram.filters import Command, CommandObject

from aiogram.types import Message

from db.database import Database

from keyboards.user_kb import main_user_panel
from keyboards.setup_ui import set_bot_commands

from utils.phrases import ErrorPhrases, Phrases

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_command(message: Message, db: Database) -> None:
    if not await db.get_user(message.from_user.id):
        await message.answer(Phrases.first_greeting())
    else:
        await message.answer(Phrases.start(), reply_markup=main_user_panel())
        await set_bot_commands(message.bot)


@router.message(Command("reg"))
async def select_group(message: Message, command: CommandObject, db: Database) -> None:
    if await db.get_user(message.from_user.id):
        await message.answer(Phrases.already_registered())
        return

    try:
        if command.args.lower() in [
            "нпк",
            "кнн",
        ]:  # заменить на реал группы. когда нибудь
            await db.create_user(
                message.from_user.id,
                message.from_user.username,
                command.args.lower(),
            )
            await message.answer(Phrases.success(), reply_markup=main_user_panel())

            logger.info("User %s registered", message.from_user.username)

        else:
            await message.answer(ErrorPhrases.group_not_found())
            return
    except TypeError as e:
        await message.reply(ErrorPhrases.invalid())
        logger.error(e)
        return
    except Exception as e:
        await message.reply(ErrorPhrases.something_went_wrong())
        logger.error(e)
