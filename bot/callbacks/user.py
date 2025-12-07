from aiogram import Router, F
from aiogram import types

from bot.db.database import Database
from bot.utils.phrases import ErrorPhrases

from core.queue_manager import get_queue_manager
from core.message_models import SelectChatDTO

router = Router()


@router.callback_query(F.data.startswith("max_chat_"))
async def select_max_chat(callback: types.CallbackQuery, db: Database) -> None:
    args = callback.data.split("_")

    if len(args) != 3:
        return

    if args[2] == "empty":
        await callback.answer(ErrorPhrases.something_went_wrong, show_alert=True)

        if callback.message:
            await callback.message.delete()
        return
    elif args[2] == "any":
        await callback.message.delete()
        return

    user = await db.get_user(callback.from_user.id)

    # Check if user is registered
    if not user:
        await callback.answer(ErrorPhrases.user_not_found(), show_alert=True)
        return

    await get_queue_manager().to_ws.put(
        SelectChatDTO(
            owner_id=user.tg_id,
            group_id=int(callback.message.chat.id),
            chat_id=int(args[2]),
            group_title=callback.message.chat.title,
        )
    )

    await callback.message.delete()
