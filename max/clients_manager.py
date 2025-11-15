import logging
import asyncio

from typing import Optional
from .client import MaxClient

logger = logging.getLogger(__name__)


class MaxManager:
    def __init__(self):
        self.clients: dict[str, MaxClient] = {}
        self.parser_queue = asyncio.Queue()

    async def add_client(self, key: int, token: str) -> None:
        """
        Create a new MaxClient with the token and add it to the parser
        The key is the User TG ID
        """

        if not token or not key:
            raise ValueError("One field is empty")

        if key in self.clients:
            raise ValueError("Client with this TG User ID already exists")

        client = MaxClient(bot_queue=self.bot_queue, token=token, tg_user_id=key)
        await client.connect()
        self.clients[key] = client

    async def start_auth(self, key: int, phone_number: str):
        """
        To get token you need to login. an sms acception will be sent to your phone
        The key is the User TG ID
        """

        if not phone_number or not key:
            raise ValueError("One of the fields is empty")

        if key in self.clients:
            raise ValueError("Client with this TG User ID already exists")

        client = MaxClient(bot_queue=self.bot_queue, tg_user_id=key)

        await client.connect(auth_with_token=True)
        await client.start_auth(phone_number)

        self.clients[key] = client

    async def check_code(self, key: int, short_token: str, code: str):
        """
        Verify code and get token
        The key is User TG ID
        """

        if not short_token or not code or not key:
            raise ValueError("All fields must be filled in")

        client = self.get_client(key)

        await client.check_code(short_token, code)

    async def remove_client(self, key: int):
        """
        Remove a MaxClient from the parser
        The key is User TG ID
        """

        if key not in self.clients:
            raise ValueError("Client with this TG User ID does not exist")

        del self.clients[key]

    def get_client(self, key: int) -> Optional[MaxClient]:
        """Get a MaxClient by its TG User ID"""

        if key not in self.clients:
            logger.warning("Client with this TG User ID does not exist")
            return None

        return self.clients[key]

    async def _startup(self):
        pass

    async def _load_clients(self):
        # Fetch Model from DB
        # Load from User Model into self.clients :: [from_db_id, from_db_token]
        pass
