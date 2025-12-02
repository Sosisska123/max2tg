# inspired by
# https://n0paste.eu/9N5uYA6/
# https://github.com/nsdkinx/vkmax/

import asyncio
import logging
import websockets
import itertools
import json

from typing import Any, Callable, Optional, Union

from functools import wraps

from core.message_models import (
    MessageModel,
    FetchChatsMessage,
    ChatMsgMessage,
    SMSConfirmedMessage,
    PhoneSentMessage,
    Attach,
    ErrorMessage,
)

from .templates.payloads import (
    get_ping_json,
    get_useragent_header_json,
    get_token_json,
    get_subscribe_json,
    get_read_last_message_json,
    get_messages_json,
    get_start_auth_json,
    get_check_code_json,
)

from .utils.date import get_unix_now

from config import config

from core.queue_manager import get_queue_manager

logger = logging.getLogger(__name__)

PING_OPCODE = 1


def ensure_connected(method: Callable):
    @wraps(method)
    async def wrapper(self, *args, **kwargs):
        if self.websocket is None:
            raise RuntimeError("WebSocket not connected. Call .connect() first.")
        return await method(self, *args, **kwargs)

    return wrapper


class MaxClient:
    def __init__(
        self,
        tg_user_id: int,
        token: str = None,
        proxy: str | bool = True,
    ):
        self.websocket: Optional[websockets.ClientConnection] = None
        self.token = token
        self.proxy = proxy
        self.tg_user_id = tg_user_id

        self._ws_url = config.ws.url
        self._seq = 0
        self._counter = itertools.count(0, 1)
        self._current_listening_chat: Optional[str] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._chat_subscription_ping_task: Optional[asyncio.Task] = None
        self._recv_task: Optional[asyncio.Task] = None

    async def connect(self, auth_with_token: bool = False):
        """
        Connect to the MAX websocket server and perform the handshake
        You'll get a token if you are logging for the first time
        Next time token will be used automatically
        """

        # TODO: turn off websocket builtin ping

        if self.websocket:
            raise Exception("Already connected")

        logger.info("⌛ Trying to connect to MAX websocket...")

        try:
            self.websocket = await websockets.connect(
                self._ws_url,
                origin=websockets.Origin("https://web.max.ru"),
                proxy=self.proxy,
            )

            # Token is generally used to collect user chats
            if auth_with_token:
                await self._handshake()
            else:
                # if token is not provided, we need to get it first
                logger.info("🔑 No token provided, getting it...")
                await self.websocket.send(get_useragent_header_json())
                self._get_next_seq()

            logger.info("✅ Connected to MAX websocket")

            self._recv_task = asyncio.create_task(self._read_messages())
            self._ping_task = asyncio.create_task(self._send_ping())

        except Exception as e:
            logger.error(f"Failed to connect to MAX websocket: {e}")
            raise

    async def disconnect(self):
        """Disconnect from the MAX websocket server."""

        if self.websocket:
            await self.websocket.close()
            if self._recv_task:
                self._recv_task.cancel()
            if self._ping_task:
                self._ping_task.cancel()
            if self._chat_subscription_ping_task:
                self._chat_subscription_ping_task.cancel()
                self.stop_listening_to_chat(self._current_listening_chat)
            self.websocket = None

            logger.info("%s -- ❌ Disconnected from MAX WebSocket", self.tg_user_id)

    @ensure_connected
    async def listen_to_chat(self, chat_id: str):
        """Listen to the specific chat for new messages"""

        if chat_id == self._current_listening_chat:
            raise ValueError("You are already listening to this chat")

        # Unsubscribe from the previous chat
        if self._current_listening_chat is not None:
            await self._subscribe_to_chat(self._current_listening_chat, False)

        await self._subscribe_to_chat(chat_id, True)
        self._current_listening_chat = chat_id

        if self._chat_subscription_ping_task is None:
            self._chat_subscription_ping_task = asyncio.create_task(
                self._chat_subscription_ping()
            )

        logger.info(f"💭 Now listening to chat {chat_id}")

    @ensure_connected
    async def stop_listening_to_chat(self, chat_id: str):
        """Stop listening to a chat"""

        if chat_id != self._current_listening_chat:
            raise ValueError("You are not listening to this chat")

        self._current_listening_chat = None

        await self._subscribe_to_chat(chat_id, False)

        logger.info(f"💭❌ Stopped listening to any chat. The last chat was: {chat_id}")

    @ensure_connected
    async def _subscribe_to_chat(self, chat_id: str, state: bool = True):
        """
        Use it before getting messages
        Subscribe or unsubscribe from a chat
        """

        logger.debug("Start/stop pinging to chat %s... | state: %s", chat_id, state)
        await self.websocket.send(
            get_subscribe_json(state, chat_id, self._get_next_seq())
        )

    @ensure_connected
    async def read_last_message(self, chat_id: int, message_id: str):
        """Mark the last message in a chat as read"""

        logger.debug(
            "Marking last message in chat %s as read... | message_id: %s",
            chat_id,
            message_id,
        )
        await self.websocket.send(
            get_read_last_message_json(
                chat_id, message_id, get_unix_now(), self._get_next_seq()
            )
        )

    @ensure_connected
    async def get_messages_from_chat(self, chat_id: int):
        """
        Get the last 30 messages from a chat
        It sends only when the chat was opened for the first time
        """

        logger.debug("Getting messages from chat %s ...", chat_id)
        await self.websocket.send(
            get_messages_json(chat_id, get_unix_now(), self._get_next_seq())
        )

    @ensure_connected
    async def start_auth(self, phone: str):
        """Start the authentication process"""

        logger.debug("Starting authentication...")
        await self.websocket.send(get_start_auth_json(phone, self._get_next_seq()))

    @ensure_connected
    async def check_code(self, token: str, code: str):
        """Check the authentication code"""

        logger.debug("Verifying code... | token: %s", token)
        await self.websocket.send(
            get_check_code_json(token, code, self._get_next_seq())
        )

    async def _extract_all_attaches(self, message: dict[str, Any]) -> list[Attach]:
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

    async def _process_opcode17(self, message: dict[str, Any]) -> None:
        """Process opcode 17: start auth, phone confirmation"""

        short_token = message.get("payload", {}).get("token")

        if short_token:
            self.token = short_token

            await self._add_message_to_queue(
                PhoneSentMessage(user_id=self.tg_user_id, short_token=short_token)
            )

            logger.debug("Phone number sent, code requested, short token received")

    async def _process_opcode18(self, message: dict[str, Any]) -> None:
        """Process opcode 18: SMS confirmation and final token"""

        token_attrs = message.get("payload", {}).get("tokenAttrs")

        if token_attrs:
            self.token = token_attrs.get("LOGIN", {}).get("token")

        await self._add_message_to_queue(
            SMSConfirmedMessage(user_id=self.tg_user_id, full_token=self.token)
        )

        logger.info("🔑 New Token received | %s", self.token)
        await self.fetch_chats()

    async def _process_opcode19(self, message: dict[str, Any]) -> None:
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
                    user_id=self.tg_user_id,
                    chat_id=chat_id,
                    chat_title=chat_title,
                    messages_count=msgs_count,
                    last_message_id=last_msg_id,
                )
            )

        await self._add_message_to_queue(chats)

    async def _process_opcode49(self, message: dict[str, Any]) -> None:
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
                    user_id=self.tg_user_id,
                    sender_id=msg_data.get("sender"),
                    message_id=msg_data.get("id"),
                    timestamp=msg_data.get("time"),
                    text=msg_data.get("text"),
                )
            )

        await self._add_message_to_queue(msgs)

    async def _process_opcode64(self, message: dict[str, Any]) -> None:
        """Process opcode 64: Collect new chat message in chat"""

        # i think it SENDS message to server
        return

        payload = message.get("payload", {})

        logger.debug(
            "New message received from chat %s ...", payload.get("chatId", "NOT CHAT")
        )

        await self._add_message_to_queue(
            ChatMsgMessage(
                user_id=self.tg_user_id,
                sender_id=payload.get("sender"),
                message_id=payload.get("id"),
                timestamp=payload.get("time"),
                text=payload.get("text"),
            )
        )

    async def _process_opcode128(self, message: dict[str, Any]) -> None:
        """Process opcode 128: Receive new message from anywhere"""

        payload = message.get("payload", {})
        message_data = payload.get("message", {})

        logger.debug(
            "New message received from chat %s ...", payload.get("chatId", "NOT CHAT")
        )

        attaches = []
        replied_msg = None

        if message_data.get("link"):
            replied_msg = message_data.get("link").get("message", {})

            attaches.extend(await self._extract_all_attaches(message_data))
            attaches.extend(await self._extract_all_attaches(replied_msg))

        await self._add_message_to_queue(
            ChatMsgMessage(
                user_id=self.tg_user_id,
                chat_id=payload.get("chatId"),
                sender_id=message_data.get("sender"),
                message_id=message_data.get("id"),
                timestamp=message_data.get("time"),
                text=message_data.get("text"),
                attaches=attaches,
                replied_msg=replied_msg,
            )
        )

    async def _add_message_to_queue(
        self, message: Union[list[MessageModel], MessageModel]
    ):
        """Add a message to the bot queue"""

        await get_queue_manager().to_bot.put(message)

    @ensure_connected
    async def process_message(self, message: dict[str, Any]):
        """Manage a received message"""

        logger.debug("Processing message: %s", message)

        match message.get("opcode", -1):
            case 17:
                await self._process_opcode17(message)
            case 18:
                await self._process_opcode18(message)
            case 19:
                await self._process_opcode19(message)
            case 49:
                await self._process_opcode49(message)
            case 64:
                await self._process_opcode64(message)
            case 128:
                await self._process_opcode128(message)
            case -1:
                logger.warning(f"Unknown opcode: {message}")
            case _:
                logger.warning(f"Unknown opcode: {message}")

    @ensure_connected
    async def fetch_chats(self):
        """
        Fetch chats using the provided auth token.
        Use if you are logging for the first time
        """

        if self.token is None:
            raise ValueError("Need to set token first")

        await self.websocket.send(get_token_json(self.token, self._get_next_seq()))

    @ensure_connected
    async def _handshake(self):
        """Perform the initial handshake with the MAX websocket server with user provided token"""

        if not self.token:
            raise ValueError("Need to set token first")

        await self.websocket.send(get_useragent_header_json())
        await self.websocket.send(get_token_json(self.token, self._get_next_seq()))

    @ensure_connected
    async def _read_messages(self):
        """Read messages from the websocket and log them"""

        while self.websocket is not None:
            try:
                raw_message = await self.websocket.recv()

                if not raw_message:
                    continue

                message = json.loads(raw_message)

                if not message:
                    continue

                logger.debug(f"Received message from MAX: {message}")

                # Handle errors
                if message.get("payload", {}).get("error", None):
                    await self._add_message_to_queue(
                        ErrorMessage(
                            user_id=self.tg_user_id,
                            message=(
                                message["payload"]["error"]
                                + "\n\n"
                                + message["payload"]["localizedMessage"]
                                + "\n\n"
                                + message["payload"]["message"]
                            ),
                        )
                    )

                    raise Exception(
                        f"💀 Error: {message['payload']['error']}: {message['payload']['localizedMessage']} || {message['payload']['message']}"
                    )

                await self.process_message(message)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("Websocket connection closed. Reconnecting...")
                # TODO: Implement controlled reconnection to avoid task leaks
                break

            except AttributeError as e:
                if isinstance(message, dict) and message.get("opcode") == PING_OPCODE:
                    continue
                logger.error(e)
                continue

            except Exception as e:
                logger.error(f"Error while reading messages from MAX: {e}")
                continue

    @ensure_connected
    async def _send_ping(self):
        """Send a ping to the server every 30 seconds"""

        while self.websocket is not None:
            await asyncio.sleep(30)
            if self.websocket is None:
                break
            await self.websocket.send(get_ping_json(self._get_next_seq()))

    @ensure_connected
    async def _chat_subscription_ping(self):
        """Send a ping to the server every 1 minute if you are listening to a chat"""

        while self._current_listening_chat is not None:
            await asyncio.sleep(60)

            if self._current_listening_chat is None:
                continue

            await self._subscribe_to_chat(self._current_listening_chat, True)

    def _get_next_seq(self) -> int:
        """Get the next sequence number."""
        self._seq = next(self._counter)
        return self._seq
