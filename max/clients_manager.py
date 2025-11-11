import logging
import asyncio

from typing import Optional
from client import MaxClient

logger = logging.getLogger(__name__)


class MaxManager:
    def __init__(self, bot_queue: asyncio.Queue):
        self.clients: dict[str, MaxClient] = {}
        self.bot_queue = bot_queue
        self.parser_queue = asyncio.Queue()

    async def add_client(self, tg_user_id: int, token: str) -> None:
        """
        Create a new MaxClient with the token and add it to the parser
        The key is the TG User ID
        """

        if not token or not tg_user_id:
            raise ValueError("One field is empty")

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

        await client.connect(auth_with_token=True)
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
