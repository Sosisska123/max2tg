import logging

from aiogram import Router
from aiogram.types import CallbackQuery

from filters.is_admin import IsAdmin

from utils.states import SubscribeMaxChat

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(IsAdmin(), SubscribeMaxChat.select_listening_chat)
async def admin_add_listening_chat_command(
    callback: CallbackQuery,
):
    await callback.answer()
    # TODO: Implement logic to add listening chat
