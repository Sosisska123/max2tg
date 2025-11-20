import logging

from aiogram import Bot

from bot.db.database import Database
from bot.db.db_dependency import DBDependency
from bot.utils.phrases import Phrases
from max.clients_manager import MaxManager

from core.queue_manager import get_queue_manager
from core.message_models import (
    FetchChatsMessage,
    GetChatMessagesMessage,
    ChatMsgMessage,
    MessageModel,
    PhoneConfirmedMessage,
    SMSConfirmedMessage,
    StartAuthMessage,
    VerifyCodeMessage,
)


logger = logging.getLogger(__name__)


async def handle_from_bot(max_manager: MaxManager) -> None:
    """Listen for commands from the bot and send them to the MAX WebSocket"""

    while True:
        try:
            msg = await get_queue_manager().to_ws.get()
            await send_to_websocket(max_manager=max_manager, msg=msg)
            get_queue_manager().to_ws.task_done()

        except Exception as e:
            logger.error("[FROM BOT] Handling error: %s", e)


async def handle_from_ws(bot: Bot, db_dependency: DBDependency) -> None:
    """Listen for commands from the MAX WebSocket and send them to the bot"""

    while True:
        try:
            msg = await get_queue_manager().to_bot.get()
            await send_to_bot(bot=bot, db_dependency=db_dependency, msg=msg)
            get_queue_manager().to_bot.task_done()

        except Exception as e:
            logger.error("[FROM BOT] Handling error: %s", e)


async def send_to_bot(
    bot: Bot, db_dependency: DBDependency, msg: MessageModel | list[FetchChatsMessage]
) -> None:
    if not msg:
        logger.error("[FROM WS] Message is empty")
        return

    # Handle the special case where msg is a list of FetchChatsMessage objects
    # This is a workaround for a design where message types are mixed (single MessageModel vs. list of models)
    # A more robust solution would involve a dedicated MessageModel for lists of chats.
    if isinstance(msg, list) and all(
        isinstance(item, FetchChatsMessage) for item in msg
    ):
        async with db_dependency.db_session() as session:
            db = Database(session=session)
            for fcmsg in msg:
                await db.store_user_max_chat(
                    chat_id=fcmsg.chat_id,
                    chat_title=fcmsg.chat_title,
                    owner_tg_id=fcmsg.user_id,
                    messages_count=fcmsg.messages_count,
                    last_message_id=fcmsg.last_message_id,
                )
        return

    # If not a list of FetchChatsMessage, proceed with the standard MessageModel matching
    if not msg.user_id:  # This check assumes msg is a MessageModel, not a list
        logger.error("[FROM WS] User ID is empty")
        return

    try:
        match msg.type:
            case "phone_confirmed":
                pcmsg = PhoneConfirmedMessage(msg)

                logger.info(
                    "📃 Phone number confirmed, waiting for sms code...| Token: %s | User ID: %s",
                    pcmsg.token,
                    pcmsg.user_id,
                )

                async with db_dependency.db_session() as session:
                    db = Database(session=session)

                    await db.update_user_max_token(pcmsg.user_id, pcmsg.token)
                    await db.update_user_max_permission(
                        pcmsg.user_id, True
                    )  # FIXME: Remove
                    await bot.send_message(pcmsg.user_id, Phrases.max_request_sms())

            case "sms_confirmed":
                scmsg = SMSConfirmedMessage(msg)

                await bot.send_message(scmsg.user_id, Phrases.max_login_success())

            case "new_chat_message":
                ncm = ChatMsgMessage(msg)
                await bot.send_message(
                    chat_id=ncm.user_id,
                    text=f"💬 New message in chat `{ncm.chat_id}`:\n\n{ncm.text}",
                    parse_mode="Markdown",
                )

            case "send_chat_list":
                pass

            case _:
                logger.error(f"Unknown action: {msg.type}")

    except Exception as e:
        logger.error(f"[FROM WS] Error while executing command from parser: {e}")


async def send_to_websocket(max_manager: MaxManager, msg: MessageModel) -> None:
    if not msg:
        logger.error("[FROM BOT] Message is empty")
        return

    if not msg.user_id:
        logger.error("[FROM BOT] User ID is empty")
        return

    try:
        match msg.type:
            case "start_auth":
                await max_manager.start_auth(msg.user_id, StartAuthMessage(msg).phone)

            case "verify_code":
                vcmsg = VerifyCodeMessage(msg)

                await max_manager.check_code(
                    key=msg.user_id,
                    short_token=vcmsg.token,
                    code=vcmsg.code,
                )

            case "get_chat_messages":
                gcmsg = GetChatMessagesMessage(msg)
                await max_manager.get_messages_from_chat(
                    key=gcmsg.user_id, chat_id=gcmsg.chat_id
                )

            case "subscribe_to_chat":
                pass

    except Exception as e:
        logger.error(
            f"[FROM BOT | EXECUTING] Error while executing command from bot: {e}"
        )
