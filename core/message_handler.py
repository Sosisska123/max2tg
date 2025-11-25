import logging
from typing import Union

from aiogram import Bot

from bot.db.database import Database
from bot.db.db_dependency import DBDependency
from bot.services.mailing_manager import forward_message_to_group
from bot.utils.phrases import Phrases
from max.clients_manager import MaxManager

from core.queue_manager import get_queue_manager
from core.message_models import (
    FetchChatsMessage,
    ChatMsgMessage,
    MessageModel,
    PhoneSentMessage,
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
            logger.error("[FROM WS] Handling error: %s", e)


async def send_to_bot(
    bot: Bot, db_dependency: DBDependency, msg: Union[MessageModel, list[MessageModel]]
) -> None:
    """Catch messages from a MAX Client and send them to the bot"""

    if isinstance(msg, list):
        if isinstance(msg[0], FetchChatsMessage):
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
        elif isinstance(msg[0], ChatMsgMessage):
            # i think it would be non-efficient to
            # send about 30 messages for each chat
            # and at the same time
            # i cant combine all the messages into 1 text
            # because of telegram max string length
            # (but maybe i can, I didn't find out)
            return
            text = ""

            for m in msg:
                cmmsg = ChatMsgMessage(msg)

                text = "\n".join(
                    f"💬 New message in chat `{cmmsg.chat_id}`: {cmmsg.text}"
                )

            await bot.send_message(
                chat_id=cmmsg.user_id,
                text=text,
            )
        return

    try:
        # idk why not using isinstance FIXME: fix
        match msg.type:
            case "phone_sent":
                psmsg = PhoneSentMessage.model_validate(msg.model_dump())

                logger.info(
                    "📃 Phone number confirmed, waiting for sms code...| Token: %s | User ID: %s",
                    psmsg.short_token,
                    psmsg.user_id,
                )

                await bot.send_message(psmsg.user_id, Phrases.max_request_sms())

            case "sms_confirmed":
                scmsg = SMSConfirmedMessage.model_validate(msg.model_dump())

                async with db_dependency.db_session() as session:
                    db = Database(session=session)

                    await db.update_user_max_token(scmsg.user_id, scmsg.full_token)
                    await db.update_user_max_permission(
                        scmsg.user_id, True
                    )  # FIXME: Leave only update_user_max_token

                await bot.send_message(scmsg.user_id, Phrases.max_login_success())

            case "new_chat_message":
                cmmsg = ChatMsgMessage.model_validate(msg.model_dump())

                async with db_dependency.db_session() as session:
                    db = Database(session=session)

                    connected_groups = await db.get_tg_groups_subscribed_to_max(
                        cmmsg.chat_id
                    )

                if not connected_groups:
                    logger.error("No subscribed groups for a chat: %s", cmmsg.chat_id)
                    return

                if cmmsg.replied_msg:
                    await forward_message_to_group(
                        bot=bot,
                        tg_group_ids=connected_groups,
                        sender_name=cmmsg.sender_id,
                        max_chat=cmmsg.chat_id,
                        message_text=cmmsg.text,
                        replied_sender_name=cmmsg.replied_msg.sender_id,
                        replied_message_text=cmmsg.replied_msg.text,
                        medias=cmmsg.attaches,
                    )
                else:
                    await forward_message_to_group(
                        bot=bot,
                        tg_group_ids=connected_groups,
                        sender_name=cmmsg.sender_id,
                        max_chat=cmmsg.chat_id,
                        message_text=cmmsg.text,
                        medias=cmmsg.attaches,
                    )

            case "send_chat_list":
                pass

            case _:
                logger.error(f"Unknown action: {msg.type}")

    except Exception as e:
        logger.error(f"[FROM WS] Error while executing command from parser: {e}")


async def send_to_websocket(max_manager: MaxManager, msg: MessageModel) -> None:
    """Catch messages from the bot and send them to the Max"""

    if not msg.user_id:
        logger.error("[FROM BOT] User ID is empty")
        return

    try:
        match msg.type:
            case "start_auth":
                await max_manager.start_auth(
                    msg.user_id, StartAuthMessage.model_validate(msg.model_dump()).phone
                )

            case "verify_code":
                vcmsg = VerifyCodeMessage.model_validate(msg.model_dump())

                await max_manager.check_code(
                    key=msg.user_id,
                    short_token=vcmsg.token,
                    code=vcmsg.code,
                )

    except Exception as e:
        logger.error(
            f"[FROM BOT | EXECUTING] Error while executing command from bot: {e}"
        )
