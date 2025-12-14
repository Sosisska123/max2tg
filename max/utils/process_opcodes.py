import logging
from typing import Any, Union

from core.message_models import (
    MessageModel,
    FetchChatsMessage,
    ChatMsgMessage,
    SMSConfirmedMessage,
    PhoneSentMessage,
    Attach,
)

from core.queue_manager import get_queue_manager

logger = logging.getLogger(__name__)


async def process_opcode17(message: dict[str, Any], tg_user_id: int) -> str:
    """Process opcode 17: start auth, phone confirmation. **Returns short token**"""

    short_token = message.get("payload", {}).get("token")

    if short_token:
        await add_message_to_queue(
            PhoneSentMessage(user_id=tg_user_id, short_token=short_token)
        )

        logger.debug("Phone number sent, code requested, short token received")

    return short_token


async def process_opcode18(message: dict[str, Any], tg_user_id: int) -> bool:
    """Process opcode 18: SMS confirmation and final token. **Returns True if token received**"""

    token_attrs = message.get("payload", {}).get("tokenAttrs")

    if token_attrs:
        token = token_attrs.get("LOGIN", {}).get("token")

        await add_message_to_queue(
            SMSConfirmedMessage(user_id=tg_user_id, full_token=token)
        )

        logger.info("🔑 New Token received | %s", token)
        return True


async def process_opcode19(message: dict[str, Any], tg_user_id: int) -> None:
    """Process opcode 19: chat list"""

    logger.debug("Collecting user information | Fetching chats...")
    chats = []

    for chat in message.get("payload", {}).get("chats", []):
        chat_id = chat.get("id")
        chat_title = chat.get("title")

        if not chat_id or not chat_title:
            continue

        msgs_count = chat.get("messagesCount", 0)
        last_message = chat.get("lastMessage")
        last_msg_id = last_message.get("id") if last_message else 0

        chats.append(
            FetchChatsMessage(
                user_id=tg_user_id,
                chat_id=chat_id,
                chat_title=chat_title,
                messages_count=msgs_count,
                last_message_id=last_msg_id,
            )
        )

        await add_message_to_queue(chats)


async def process_opcode49(message: dict[str, Any], tg_user_id: int) -> None:
    """Process opcode 49: get last 30 chat messages"""

    payload = message.get("payload", {})

    logger.debug("Collecting messages from chat...")

    msgs = []

    for msg_data in payload.get("messages", []):
        # NOTE: Attr "attaches" on default messages usually have chat events
        #       like joinByLink, leave, add
        #       But on linked messages it may contain media (like photo)
        #       Now we're not extracting photos beacuse it would be a lot of media

        msgs.append(
            ChatMsgMessage(
                user_id=tg_user_id,
                sender_id=msg_data.get("sender"),
                message_id=msg_data.get("id"),
                timestamp=msg_data.get("time"),
                text=msg_data.get("text"),
            )
        )

    await add_message_to_queue(msgs)


async def process_opcode64(message: dict[str, Any], tg_user_id: int) -> None:
    """Process opcode 64: Collect new chat message in chat"""

    # i think it SENDS message to server
    return

    payload = message.get("payload", {})

    logger.debug(
        "New message received from chat %s ...", payload.get("chatId", "NOT CHAT")
    )

    await add_message_to_queue(
        ChatMsgMessage(
            user_id=tg_user_id,
            sender_id=payload.get("sender"),
            message_id=payload.get("id"),
            timestamp=payload.get("time"),
            text=payload.get("text"),
        )
    )


async def process_opcode128(message: dict[str, Any], tg_user_id: int) -> None:
    """Process opcode 128: Receive new message from anywhere"""

    payload = message.get("payload", {})
    message_data = payload.get("message", {})

    logger.debug(
        "New message received from chat %s ...", payload.get("chatId", "NOT CHAT")
    )

    attaches = []
    replied_msg = None

    attaches.extend(await extract_all_attaches(message_data))

    if message_data.get("link"):
        replied_msg_raw = message_data.get("link").get("message", {})

        if replied_msg_raw:
            replied_msg = ChatMsgMessage(
                user_id=tg_user_id,
                chat_id=payload.get("chatId"),
                sender_id=replied_msg_raw.get("sender"),
                message_id=replied_msg_raw.get("id"),
                timestamp=replied_msg_raw.get("time"),
                text=replied_msg_raw.get("text"),
            )

        attaches.extend(await extract_all_attaches(replied_msg_raw))

    await add_message_to_queue(
        ChatMsgMessage(
            user_id=tg_user_id,
            chat_id=payload.get("chatId"),
            sender_id=message_data.get("sender"),
            message_id=message_data.get("id"),
            timestamp=message_data.get("time"),
            text=message_data.get("text"),
            attaches=attaches,
            replied_msg=replied_msg,
        )
    )


async def add_message_to_queue(message: Union[list[MessageModel], MessageModel]):
    """Add a message to the bot queue"""

    await get_queue_manager().to_bot.put(message)


async def extract_all_attaches(message: dict[str, Any]) -> list[Attach]:
    """
    This method is used to extract all attaches from a message
    """

    attaches = []

    for attach in message.get("attaches", []):
        # TODO: Add other types support
        if attach.get("_type") != "PHOTO":
            continue

        at = Attach(base_url=attach.get("baseUrl"))
        attaches.append(at)

    return attaches
