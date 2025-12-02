import logging
from typing import Union

from aiogram import Bot

from bot.db.database import Database
from bot.db.db_dependency import DBDependency
from bot.services.mailing_manager import forward_message_to_group
from bot.utils.phrases import Phrases, ErrorPhrases

from max.db.max_repo import MaxRepository
from max.clients_manager import MaxManager
from max.utils.user_keyboard import max_chats_inline_kb

from core.queue_manager import get_queue_manager
from core.message_models import (
    DTO,
    SubscribeGroupDTO,
    FetchChatsMessage,
    ChatMsgMessage,
    MessageModel,
    PhoneSentMessage,
    SMSConfirmedMessage,
    StartAuthMessage,
    VerifyCodeMessage,
    SelectChatDTO,
    ErrorMessage,
)


logger = logging.getLogger(__name__)


async def handle_from_bot(
    bot: Bot, max_manager: MaxManager, db_dependency: DBDependency
) -> None:
    """Listen for commands from the bot and send them to the MAX WebSocket"""

    while True:
        try:
            msg = await get_queue_manager().to_ws.get()

            await send_to_websocket(
                max_manager=max_manager,
                msg=msg,
                db_dependency=db_dependency,
                bot=bot,
            )
            get_queue_manager().to_ws.task_done()

        except Exception as e:
            logger.error("[FROM BOT] Handling error: %s", e)


async def handle_from_ws(
    bot: Bot, db_dependency: DBDependency, bot_db_dependency: DBDependency
) -> None:
    """Listen for commands from the MAX WebSocket and send them to the bot"""

    while True:
        try:
            msg = await get_queue_manager().to_bot.get()
            await send_to_bot(
                bot=bot,
                db_dependency=db_dependency,
                msg=msg,
                bot_db_dependency=bot_db_dependency,
            )
            get_queue_manager().to_bot.task_done()

        except Exception as e:
            logger.error("[FROM WS] Handling error: %s", e)


async def send_to_bot(
    bot: Bot,
    db_dependency: DBDependency,
    msg: Union[MessageModel, list[MessageModel]],
    bot_db_dependency: DBDependency,
) -> None:
    """Catch messages from a MAX Client and send them to the bot"""

    if isinstance(msg, list):
        if not msg:
            logger.warning("[FROM WS] Received empty message list")
            return

        if isinstance(msg[0], FetchChatsMessage):
            async with db_dependency.db_session() as session:
                db = MaxRepository(session=session)

                for raw_fcmsg in msg:
                    fcmsg = FetchChatsMessage.model_validate(raw_fcmsg.model_dump())

                    await db.save_user_chat(
                        owner_id=fcmsg.user_id,
                        chat_id=fcmsg.chat_id,
                        chat_title=fcmsg.chat_title,
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
                cmmsg = ChatMsgMessage.model_validate(m.model_dump())

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
                    "📃 Phone number confirmed, waiting for sms code...| Short Token: %s | User ID: %s",
                    psmsg.short_token,
                    psmsg.user_id,
                )

                # Save account with the short token
                async with db_dependency.db_session() as session:
                    db = MaxRepository(session=session)

                    await db.save_account(psmsg.user_id, psmsg.short_token)

                await bot.send_message(psmsg.user_id, Phrases.max_request_sms())

            case "sms_confirmed":
                scmsg = SMSConfirmedMessage.model_validate(msg.model_dump())

                # Update user token
                async with db_dependency.db_session() as session:
                    db = MaxRepository(session=session)

                    await db.set_user_token(scmsg.user_id, scmsg.full_token)

                # FIXME:
                async with bot_db_dependency.db_session() as session:
                    db = Database(session=session)

                    await db.update_connection_state(scmsg.user_id, True)

                await bot.send_message(scmsg.user_id, Phrases.max_login_success())

            case "new_chat_message":
                cmmsg = ChatMsgMessage.model_validate(msg.model_dump())

                async with db_dependency.db_session() as session:
                    db = MaxRepository(session=session)

                    connected_groups = await db.get_groups_include_any(cmmsg.chat_id)

                if not connected_groups:
                    logger.error("No subscribed groups for a chat: %s", cmmsg.chat_id)

                    return

                ids = [group.group_id for group in connected_groups]

                if cmmsg.replied_msg:
                    await forward_message_to_group(
                        bot=bot,
                        tg_group_ids=ids,
                        sender_name=cmmsg.sender_id,
                        max_chat=cmmsg.chat_id,
                        message_text=cmmsg.text,
                        replied_sender_name=cmmsg.replied_msg.sender_id,
                        replied_text=cmmsg.replied_msg.text,
                        medias=cmmsg.attaches,
                    )
                else:
                    await forward_message_to_group(
                        bot=bot,
                        tg_group_ids=ids,
                        sender_name=cmmsg.sender_id,
                        max_chat=cmmsg.chat_id,
                        message_text=cmmsg.text,
                        medias=cmmsg.attaches,
                    )

            case "send_chat_list":
                pass

            case "error":
                emsg = ErrorMessage.model_validate(msg.model_dump())

                await bot.send_message(emsg.user_id, emsg.message)

            case _:
                logger.error(f"Unknown action: {msg.type}")

    except Exception as e:
        logger.error(f"[FROM WS] Error while executing command from parser: {e}")


async def send_to_websocket(
    max_manager: MaxManager, msg: MessageModel, db_dependency: DBDependency, bot: Bot
) -> None:
    """Catch messages from the bot and send them to the Max"""

    if not isinstance(msg, DTO) and not msg.user_id:
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

                token = vcmsg.token

                if token is None:
                    async with db_dependency.db_session() as session:
                        db = MaxRepository(session=session)
                        token = await db.get_user_token(vcmsg.user_id)

                await max_manager.check_code(
                    key=msg.user_id,
                    short_token=token,
                    code=vcmsg.code,
                )

            case "sub_group":
                scdto = SubscribeGroupDTO.model_validate(msg.model_dump())
                chats_list = None

                async with db_dependency.db_session() as session:
                    db = MaxRepository(session=session)
                    group = await db.get_group(scdto.group_id)

                    if group:
                        await bot.send_message(
                            scdto.group_id,
                            ErrorPhrases.group_already_connected(scdto.group_title),
                        )
                        return

                    chats_list = await db.get_max_available_chats(scdto.owner_id)

                    if not chats_list:
                        raise ValueError("No available chats")

                logger.debug(
                    "Trying to add Group: %s | User ID: %s | Group ID: %s",
                    scdto.group_title,
                    scdto.owner_id,
                    scdto.group_id,
                )

                g = await db.add_group(
                    owner_id=scdto.owner_id,
                    group_title=scdto.group_title,
                    group_id=scdto.group_id,
                )

                if g:
                    await bot.send_message(
                        scdto.group_id,
                        Phrases.group_connected_success(
                            scdto.group_title, scdto.group_id, "None"
                        ),
                        reply_markup=max_chats_inline_kb(chats_list),
                    )
                else:
                    await bot.send_message(
                        scdto.group_id,
                        ErrorPhrases.something_went_wrong(),
                    )

            case "unsub_group":
                scdto = SubscribeGroupDTO.model_validate(msg.model_dump())

                async with db_dependency.db_session() as session:
                    db = MaxRepository(session=session)
                    group = await db.get_group(scdto.group_id)

                    if not group:
                        await bot.send_message(
                            scdto.group_id,
                            ErrorPhrases.group_never_connected(scdto.group_title),
                        )

                        return

                    if group.user_tg_id != scdto.owner_id:
                        await bot.send_message(
                            scdto.group_id,
                            Phrases.max_same_user_error(group.user_tg_id),
                        )
                        return

                logger.debug(
                    "Trying to remove Group: %s | User ID: %s | Group ID: %s",
                    scdto.group_title,
                    scdto.owner_id,
                    scdto.group_id,
                )

                r = await db.remove_group(
                    group_id=scdto.group_id,
                )

                if r:
                    await bot.send_message(
                        scdto.group_id,
                        Phrases.group_disconnected_success(scdto.group_title),
                    )

                else:
                    await bot.send_message(
                        scdto.group_id,
                        ErrorPhrases.something_went_wrong(),
                    )

            case "select_chat":
                scdto = SelectChatDTO.model_validate(msg.model_dump())

                async with db_dependency.db_session() as session:
                    db = MaxRepository(session=session)
                    group = await db.get_group(scdto.group_id)

                    if not group:
                        await bot.send_message(
                            scdto.group_id,
                            ErrorPhrases.group_never_connected(scdto.group_title),
                        )
                        return

                    if group.user_tg_id != scdto.owner_id:
                        await bot.send_message(
                            scdto.group_id,
                            Phrases.max_same_user_error(group.user_tg_id),
                        )
                        return

                    r = await db.connect_group_to_chat(
                        group_id=scdto.group_id,
                        chat_id=scdto.chat_id,
                    )

                    if r:
                        await bot.send_message(
                            scdto.group_id,
                            Phrases.max_chat_connection_success(scdto.chat_id),
                        )

                        await max_manager.subscribe_to_chat(
                            key=scdto.owner_id, chat_id=scdto.chat_id
                        )

                    else:
                        await bot.send_message(
                            scdto.group_id,
                            ErrorPhrases.something_went_wrong(),
                        )

    except Exception as e:
        logger.error(
            f"[FROM BOT | EXECUTING] Error while executing command from bot: {e}"
        )
