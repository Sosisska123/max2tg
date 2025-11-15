import logging

from aiogram import Bot

from bot.db.database import Database
from bot.db.db_dependency import DBDependency
from bot.utils.phrases import Phrases
from max.clients_manager import MaxManager

from core.queue_manager import queue_manager
from core.message_models import (
    FetchChatsMessage,
    MessageModel,
    PhoneConfirmedMessage,
    SMSConfirmedMessage,
    StartAuthMessage,
    VerifyCodeMessage,
)


logger = logging.getLogger(__name__)


async def handle_from_bot(bot: Bot, db_dependency: DBDependency) -> None:
    """Listen for commands from the bot and send them to the MAX WebSocket"""

    while True:
        try:
            msg = await queue_manager.to_ws.get()
            await send_to_websocket(bot, db_dependency, msg)
            queue_manager.to_ws.task_done()

        except Exception as e:
            logger.error("[FROM BOT] Handling error: %s", e)


async def handle_from_ws(max_manager: MaxManager) -> None:
    """Listen for commands from the MAX WebSocket and send them to the bot"""

    while True:
        try:
            msg = await queue_manager.to_bot.get()
            await send_to_bot(max_manager, msg)
            queue_manager.to_bot.task_done()

        except Exception as e:
            logger.error("[FROM BOT] Handling error: %s", e)


async def send_to_bot(bot: Bot, db_dependency: DBDependency, msg: MessageModel) -> None:
    if not msg:
        logger.error("[FROM WS] Message is empty")
        return

    if not msg.user_id:
        logger.error("[FROM WS] User ID is empty")
        return

    try:
        match msg.type:
            case "phone_confirmed":
                pcmsg = PhoneConfirmedMessage(msg)

                if not pcmsg:
                    logger.error("Type casting failed")
                    return

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

                if not scmsg:
                    logger.error("Type casting failed")
                    return

                await bot.send_message(scmsg.user_id, Phrases.max_login_success())

            case "fetch_chats":
                fcmsg = FetchChatsMessage(msg)

                if not fcmsg:
                    logger.error("Type casting failed")
                    return

                async with db_dependency.db_session() as session:
                    db = Database(session=session)

                    for chat in fcmsg.all_message.get("payload", {}).get("chats", []):
                        chat_id = chat.get("id", None)
                        chat_title = chat.get("title", None)

                        if not chat_id or not chat_title:
                            continue

                        msgs_count = chat.get("messagesCount", None)
                        last_msg_id = chat.get("lastMessage").get("id", None)

                        await db.store_user_max_chat(
                            chat_id=chat_id,
                            chat_title=chat_title,
                            owner_tg_id=fcmsg.user_id,
                            messages_count=msgs_count,
                            last_message_id=last_msg_id,
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

            case "subscribe_to_chat":
                pass

    except Exception as e:
        logger.error(
            f"[FROM BOT | EXECUTING] Error while executing command from bot: {e}"
        )
