import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.db.database import Database
from bot.filters.is_admin import IsAdmin
from bot.utils.phrases import AdminPhrases, ErrorPhrases


router = Router()
logger = logging.getLogger(__name__)


@router.message(Command(AdminPhrases.command_list_subscribed_groups_max), IsAdmin())
async def admin_max_get_subscribed_groups(message: Message, db: Database) -> None:
    """
    List all subscribed Telegram groups
    """

    groups = await db.get_tg_groups_list()

    if groups is None:
        await message.answer(ErrorPhrases.something_went_wrong())
        return

    output = "\n".join(
        f"{group.title}: {group.group_id} | {group.tg_id}" for group in groups
    )
    await message.answer(output if output else "No subscribed groups found.")
