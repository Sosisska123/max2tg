# https://n0paste.eu/9N5uYA6/
# https://github.com/nsdkinx/vkmax/

import asyncio
import logging
import websockets
import itertools
import json

from typing import Any, Callable, Optional

from functools import wraps

from parser.templates.payloads import (
    get_ping_json,
    get_useragent_header_json,
    get_token_json,
    get_subscribe_json,
    get_read_last_message_json,
    get_messages_json,
    get_start_auth_json,
    get_check_code_json,
)


from parser.utils.date import get_unix_now
from .config import config

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
        proxy: str = None,
    ):
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.token = token
        self.seq = itertools.count(0, 1)
        self.ws_url = config.ws_url
        self.bot_queue = bot_queue
        self.proxy = proxy
        self.tg_user_id = tg_user_id

        self._counter = itertools.count(0, 1)
        self._current_listening_chat: Optional[str] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._chat_subscription_ping_task: Optional[asyncio.Task] = None
        self._recv_task: Optional[asyncio.Task] = None

    async def connect(self, without_token: bool = False):
        """Connect to the MAX websocket server and perform the handshake"""

        if self.websocket:
            raise Exception("Already connected")

        logger.info("⌛ Connecting to MAX websocket...")

        try:
            self.websocket = await websockets.connect(
                self.ws_url,
                origin=websockets.Origin("https://web.max.ru"),
                # proxy=self.proxy if self.proxy else True,
            )

            if not without_token:
                await self._handshake()
            else:
                await self.websocket.send(get_useragent_header_json())
                self.seq = next(self._counter)

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
        await self.websocket.send(get_subscribe_json(state, chat_id, self.seq))
        self.seq = next(self._counter)

    @ensure_connected
    async def read_last_message(self, chat_id: int, message_id: str):
        """Mark the last message in a chat as read"""

        logger.debug(
            "Marking last message in chat %s as read... | message_id: %s",
            chat_id,
            message_id,
        )
        await self.websocket.send(
            get_read_last_message_json(chat_id, message_id, get_unix_now(), self.seq)
        )
        self.seq = next(self._counter)

    @ensure_connected
    async def get_messages_from_chat(self, chat_id: int):
        """Get messages from a chat. It sends only when the chat was opened for the first time"""

        logger.debug("Getting messages from chat %s ...", chat_id)
        await self.websocket.send(get_messages_json(chat_id, get_unix_now(), self.seq))
        self.seq = next(self._counter)

    @ensure_connected
    async def start_auth(self, phone: str):
        """Start the authentication process"""

        logger.debug("Starting authentication...")
        await self.websocket.send(get_start_auth_json(phone, self.seq))
        self.seq = next(self._counter)

    @ensure_connected
    async def check_code(self, token: str, code: str):
        """Check the authentication code"""

        logger.debug("Verifying code... | token: %s", token)
        await self.websocket.send(get_check_code_json(token, code, self.seq))
        self.seq = next(self._counter)

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
        self.seq = next(self._counter)

    @ensure_connected
    async def _handshake(self):
        """Perform the initial handshake with the MAX websocket server"""

        await self.websocket.send(get_useragent_header_json())
        await self.websocket.send(get_token_json(self.token))

        self.seq = next(self._counter)

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
            await self.websocket.send(get_ping_json(self.seq))
            self.seq = next(self._counter)

    @ensure_connected
    async def _chat_subscription_ping(self):
        """Send a ping to the server every 1 minute if you are listening to a chat"""

        while self._current_listening_chat is not None:
            await asyncio.sleep(60)

            if self._current_listening_chat is None:
                continue

            await self.subscribe_to_chat(self._current_listening_chat, True)
            self.seq = next(self._counter)


class MaxParser:
    def __init__(self, bot_queue: asyncio.Queue):
        self.clients: dict[str, MaxClient] = {}
        self.bot_queue = bot_queue
        self.parser_queue = asyncio.Queue()

    async def add_client(self, tg_user_id: int, token: str):
        """
        Create a new MaxClient with the token and add it to the parser
        The key is the TG User ID
        """

        if not token or not tg_user_id:
            raise ValueError("Token cannot be empty")

        if tg_user_id in self.clients:
            raise ValueError("Client with this TG User ID already exists")

        client = MaxClient(bot_queue=self.bot_queue, token=token, tg_user_id=tg_user_id)
        await client.connect()
        self.clients[tg_user_id] = client

    async def start_auth(self, tg_user_id: int, phone_number: str):
        """
        To get token you need to login. an sms acception will be sent to your phone
        The key is the TG User ID
        """

        if not phone_number or not tg_user_id:
            raise ValueError("One of the fields is empty")

        if tg_user_id in self.clients:
            raise ValueError("Client with this TG User ID already exists")

        client = MaxClient(bot_queue=self.bot_queue, tg_user_id=tg_user_id)

        await client.connect(without_token=True)
        await client.start_auth(phone_number)

        self.clients[tg_user_id] = client

    async def check_code(self, tg_user_id: int, short_token: str, code: str):
        """Verify code and get token"""

        if not short_token or not code or not tg_user_id:
            raise ValueError("All fields must be filled in")

        client = self.get_client(tg_user_id)

        await client.check_code(short_token, code)

    async def remove_client(self, tg_user_id: int):
        """Remove a MaxClient from the parser"""

        if tg_user_id not in self.clients:
            raise ValueError("Client with this TG User ID does not exist")

        del self.clients[tg_user_id]

    def get_client(self, tg_user_id: int) -> Optional[MaxClient]:
        """Get a MaxClient by its TG User ID"""

        if tg_user_id not in self.clients:
            logger.warning("Client with this TG User ID does not exist")
            return None

        return self.clients[tg_user_id]

    async def listen_for_commands(self):
        """Listen for commands from the bot and execute them."""

        while True:
            command = await self.parser_queue.get()
            try:
                action = command.get("action")
                user_id = command.get("user_id", None)
                data = command.get("data")

                match action:
                    case "start_auth":
                        await self.start_auth(user_id, data.get("phone"))

                    case "verify_code":
                        await self.check_code(
                            user_id, data.get("token"), data.get("code")
                        )

                    case "subscribe_to_chat":
                        client = self.get_client(user_id)

                        if not client:
                            continue

                        await client.listen_to_chat(data.get("chat_id"))

            except Exception as e:
                logger.error(f"Error while executing command from bot: {e}")

            finally:
                self.parser_queue.task_done()
