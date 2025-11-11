from aiogram import Router, F
from aiogram import types

from db.database import Database
from parser.client import MaxParser
from utils.phrases import ErrorPhrases, Phrases


router = Router()


@router.callback_query(F.data.startswith("max_chat_"))
async def select_max_chat(
    callback: types.CallbackQuery, db: Database, parser: MaxParser
) -> None:
    args = callback.data.split("_")

    if len(args) != 3:
        return

    if args[2] == "empty":
        await callback.answer(ErrorPhrases.something_went_wrong, show_alert=True)
        await callback.message.delete()
        return

    user = await db.get_user(callback.from_user.id)

    # Check if user is registered
    if not user:
        await callback.answer(ErrorPhrases.user_not_found(), show_alert=True)
        return

    tg_group = await db.get_tg_group_by_id(callback.message.chat.id)

    if not tg_group:
        await callback.answer(
            ErrorPhrases.chat_never_connected(callback.message.chat.title),
            show_alert=True,
        )
        return

    # Only the same user can subscribe it
    if tg_group.creator_id != user.tg_id:
        await callback.answer(Phrases.max_same_user_error(), show_alert=True)
        return

    max_chat_id = args[2]

    r = await db.connect_tg_max(tg_group.self_id, max_chat_id)

    if r:
        await callback.answer(Phrases.max_chat_connection_success(max_chat_id))
    else:
        await callback.answer(Phrases.max_chat_connection_error(max_chat_id))

    await parser.parser_queue.put(
        {
            "action": "subscribe_chat",
            "user_id": callback.from_user.id,
            "data": {"subscribed_max_chat": max_chat_id},
        }
    )

    await callback.message.delete()
