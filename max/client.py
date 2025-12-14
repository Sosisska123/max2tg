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

from core.message_models import (
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
from .utils.process_opcodes import (
    process_opcode128,
    process_opcode17,
    process_opcode18,
    process_opcode19,
    process_opcode49,
    process_opcode64,
)

from config import config


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
        self.user_tg_id = tg_user_id

        self._ws_url = config.ws.url
        self._seq = 0
        self._counter = itertools.count(0, 1)
        self._current_listening_chat: Optional[str] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._chat_subscription_ping_task: Optional[asyncio.Task] = None
        self._recv_task: Optional[asyncio.Task] = None

    async def connect(self, auth_with_token: bool = False):
        """
        Connect to the MAX WebSocket server and perform the handshake

        You need to get a token if you are logging in for the first time
        Next time token will be used to authenticate
        """

        # TODO: turn off websocket builtin ping
        # TODO: Add proxy support

        if self.websocket:
            raise Exception("Already connected")

        logger.info("⌛ Trying to connect to MAX WebSocket...")

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

            logger.info("%s -- ✅ Connected to MAX WebSocket", self.user_tg_id)

            self._recv_task = asyncio.create_task(self._receive_message_from_ws())
            self._ping_task = asyncio.create_task(self._send_ping())

        except Exception as e:
            logger.error(
                "%s -- ❌ Failed to connect to MAX WebSocket: %s", self.user_tg_id, e
            )
            raise

    async def disconnect(self):
        """Disconnect from the MAX WebSocket server"""

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
            self._seq = 0
            self._counter = itertools.count(0, 1)
            self._current_listening_chat = None

            logger.info("%s -- ❌ Disconnected from MAX WebSocket", self.user_tg_id)

    @ensure_connected
    async def listen_to_chat(self, chat_id: str):
        """Listen to the specific chat for new messages. ps: not necessary"""

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
        Update subscription to a chat. ps: not necessary
        """

        logger.debug("Start/stop pinging to chat %s... | state: %s", chat_id, state)
        await self.websocket.send(
            get_subscribe_json(state, chat_id, self._get_next_seq())
        )

    @ensure_connected
    async def read_last_message(self, chat_id: int, message_id: str):
        """Mark the last message in a chat as read. ps: not necessary"""

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

        logger.info("Getting messages from chat %s ...", chat_id)
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
        """Verify the authentication code"""

        logger.debug("Verifying code... | token: %s", token)
        await self.websocket.send(
            get_check_code_json(token, code, self._get_next_seq())
        )

    @ensure_connected
    async def process_message(self, message: dict[str, Any]):
        """Manage a received message"""

        logger.debug("Processing message: %s", message)

        match message.get("opcode", -1):
            case 17:
                token = await process_opcode17(message, self.user_tg_id)

                if not token:
                    logger.error("User auth failed. User: %s", self.user_tg_id)
                    return

                self.token = token
            case 18:
                if await process_opcode18(message, self.user_tg_id):
                    self.fetch_chats()
            case 19:
                await process_opcode19(message, self.user_tg_id)
            case 49:
                await process_opcode49(message, self.user_tg_id)
            case 64:
                await process_opcode64(message, self.user_tg_id)
            case 128:
                await process_opcode128(message, self.user_tg_id)
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
    async def _receive_message_from_ws(self):
        """Receive messages from the websocket and log them"""

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
                            user_id=self.user_tg_id,
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
                await self.disconnect()
                await self.connect()
                # TODO: add reconnection limit
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
