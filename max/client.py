# inspired by
# https://n0paste.eu/9N5uYA6/
# https://github.com/nsdkinx/vkmax/

import asyncio
import logging
import websockets
import itertools
import json

from typing import Any, Callable, Optional

from functools import wraps

from templates.payloads import (
    get_ping_json,
    get_useragent_header_json,
    get_token_json,
    get_subscribe_json,
    get_read_last_message_json,
    get_messages_json,
    get_start_auth_json,
    get_check_code_json,
)

from utils.date import get_unix_now
from config import config

logging.basicConfig(
    level=logging.INFO,
    datefmt=config.logging.date_format,
    format=config.logging.log_format,
)

logger = logging.getLogger(__name__)


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
        bot_queue: asyncio.Queue,
        tg_user_id: int,
        token: str = None,
        proxy: str | bool = True,
    ):
        self.websocket: Optional[websockets.ClientConnection] = None
        self.token = token
        self.bot_queue = bot_queue
        self.proxy = proxy
        self.tg_user_id = tg_user_id

        self._ws_url = config.ws_url
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

        if self.websocket:
            raise Exception("Already connected")

        logger.info("⌛ Trying to connect to MAX websocket...")

        try:
            self.websocket = await websockets.connect(
                self._ws_url,
                origin=websockets.Origin("https://web.max.ru"),
                proxy=self.proxy,
            )

            if auth_with_token:
                await self._handshake()
            else:
                await self.websocket.send(get_useragent_header_json())
                self._seq = next(self._counter)

            logger.info("✅ Connected to MAX websocket")

            self._recv_task = asyncio.create_task(self._read_messages())
            self._ping_task = asyncio.create_task(self._send_ping())

        except Exception as e:
            logger.error(f"Failed to connect to MAX websocket: {e}")
            raise

    @ensure_connected
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
            self.websocket = None

            logger.info("❌ Disconnected from MAX websocket")

    @ensure_connected
    async def listen_to_chat(self, chat_id: str):
        """Listen to a chat for new messages"""

        if chat_id is None:
            raise ValueError("Chat ID cannot be empty")

        if chat_id == self._current_listening_chat:
            raise ValueError("You are already listening to this chat")

        if self._current_listening_chat is not None:
            await self.subscribe_to_chat(self._current_listening_chat, False)

        await self.subscribe_to_chat(chat_id, True)
        self._current_listening_chat = chat_id

        if self._chat_subscribtion_ping_task is None:
            self._chat_subscribtion_ping_task = asyncio.create_task(
                self._chat_subscription_ping()
            )

        logger.info(f"💭 Now listening to chat {chat_id}")

    @ensure_connected
    async def stop_listening_to_chat(self, chat_id: str):
        """Stop listening to a chat"""

        if chat_id is None:
            raise ValueError("Chat ID cannot be empty")

        if chat_id != self._current_listening_chat:
            raise ValueError("You are not listening to this chat")

        self._current_listening_chat = None

        await self.subscribe_to_chat(chat_id, False)

        logger.info(f"💭❌ Stopped listening to any chat. The last chat was: {chat_id}")

    @ensure_connected
    async def subscribe_to_chat(self, chat_id: str, state: bool = True):
        """Ping it every 1 minute if your listening to a chat. Use it before getting messages
        Subscribe or unsubscribe from a chat"""

        logger.debug("Start/stop pinging to chat %s... | state: %s", chat_id, state)
        await self.websocket.send(get_subscribe_json(state, chat_id, self._seq))
        self._seq = next(self._counter)

    @ensure_connected
    async def read_last_message(self, chat_id: int, message_id: str):
        """Mark the last message in a chat as read"""

        logger.debug(
            "Marking last message in chat %s as read... | message_id: %s",
            chat_id,
            message_id,
        )
        await self.websocket.send(
            get_read_last_message_json(chat_id, message_id, get_unix_now(), self._seq)
        )
        self._seq = next(self._counter)

    @ensure_connected
    async def get_messages_from_chat(self, chat_id: int):
        """Get messages from a chat. It sends only when the chat was opened for the first time"""

        logger.debug("Getting messages from chat %s ...", chat_id)
        await self.websocket.send(get_messages_json(chat_id, get_unix_now(), self._seq))
        self._seq = next(self._counter)

    @ensure_connected
    async def start_auth(self, phone: str):
        """Start the authentication process"""

        logger.debug("Starting authentication...")
        await self.websocket.send(get_start_auth_json(phone, self._seq))
        self._seq = next(self._counter)

    @ensure_connected
    async def check_code(self, token: str, code: str):
        """Check the authentication code"""

        logger.debug("Verifying code... | token: %s", token)
        await self.websocket.send(get_check_code_json(token, code, self._seq))
        self._seq = next(self._counter)

    @ensure_connected
    async def process_message(self, message: dict[str, Any]):
        """Manage a received message"""

        logger.debug("Processing message: %s", message)

        match message.get("opcode", -1):
            case 17:
                short_token = message.get("payload", {}).get("token", None)
                self.token = short_token

                await self.bot_queue.put(
                    {
                        "action": "phone_confirmed",
                        "user_id": self.tg_user_id,
                        "data": {"token": short_token},
                    }
                )

                logger.debug("Phone number sent, code requested, short token received")

            case 18:
                token_attrs = message.get("payload", {}).get("tokenAttrs", None)

                if token_attrs:
                    self.token = token_attrs.get("LOGIN", None).get("token")

                await self.bot_queue.put(
                    {
                        "action": "sms_confirmed",
                        "user_id": self.tg_user_id,
                        "data": {},
                    }
                )

                logger.info("🔑 New Token received | %s", self.token)

                # Fetching chats
                await self._fetch_chats()

            case 19:
                logger.debug("Collecting user information | Fetching chats...")

                await self.bot_queue.put(
                    {
                        "action": "fetch_chats",
                        "user_id": self.tg_user_id,
                        "data": {"all_message": message},
                    }
                )

            case 49:
                logger.debug("Collecting chat messages...")

            case -1:
                logger.warning(f"Unknown opcode: {message}")
            case _:
                logger.warning(f"Unknown opcode: {message}")

    @ensure_connected
    async def _fetch_chats(self):
        """
        Fetch chats using the provided auth token.
        Use if you are logging for the first time
        """

        if self.token is None:
            raise ValueError("Need to set token first")

        await self.websocket.send(get_token_json(self.token))
        self._seq = next(self._counter)

    @ensure_connected
    async def _handshake(self):
        """Perform the initial handshake with the MAX websocket server with user provided token"""

        if not self.token:
            raise ValueError("Need to set token first")

        await self.websocket.send(get_useragent_header_json())
        await self.websocket.send(get_token_json(self.token))

        self._seq = next(self._counter)

    @ensure_connected
    async def _read_messages(self):
        """Read messages from the websocket and log them"""

        while self.websocket is not None:
            try:
                raw_message = await self.websocket.recv()

                if not raw_message:
                    continue

                message = json.loads(raw_message)

                logger.debug(f"Received message from MAX: {message}")

                # Handle errors
                if message.get("payload", {}).get("error", None):
                    raise Exception(
                        f"💀 Error: {message['payload']['error']}: {message['payload']['localizedMessage']}"
                    )

                elif message.get("payload", None):
                    pass

                await self.process_message(message)

            except websockets.exceptions.ConnectionClosed:
                logger.warning("Websocket connection closed. Reconnecting...")
                # TODO: Implement controlled reconnection to avoid task leaks
                break

            except Exception as e:
                logger.error(f"Error while reading messages from MAX: {e}")

    @ensure_connected
    async def _send_ping(self):
        """Send a ping to the server every 30 seconds"""

        while self.websocket is not None:
            await asyncio.sleep(30)
            await self.websocket.send(get_ping_json(self._seq))
            self._seq = next(self._counter)

    @ensure_connected
    async def _chat_subscription_ping(self):
        """Send a ping to the server every 1 minute if you are listening to a chat"""

        while self._current_listening_chat is not None:
            await asyncio.sleep(60)

            if self._current_listening_chat is None:
                continue

            await self.subscribe_to_chat(self._current_listening_chat, True)
            self._seq = next(self._counter)
