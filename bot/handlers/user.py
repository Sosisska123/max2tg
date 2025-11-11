import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from db.database import Database

from keyboards.user_kb import reply_startup_kb
from keyboards.setup_ui import set_bot_commands

from utils.phrases import ErrorPhrases, Phrases

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_command(message: Message, db: Database) -> None:
    if not await db.get_user(message.from_user.id):
        await message.answer(Phrases.first_greeting())
    else:
        # Show keyboard only if chat is private

        if message.chat.type == "private":
            await message.answer(Phrases.start(), reply_markup=reply_startup_kb())
        else:
            await message.answer(Phrases.start())

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
        ]:  # todo заменить на реал группы. когда нибудь
            await db.create_user(
                message.from_user.id,
                message.from_user.username,
                command.args.lower(),
            )

            # Show keyboard only if chat is private

            if message.chat.type == "private":
                await message.answer(Phrases.success(), reply_markup=reply_startup_kb())
            else:
                await message.answer(Phrases.success())

            logger.info("User %s registered", message.from_user.username)

            await set_bot_commands(message.bot)

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
