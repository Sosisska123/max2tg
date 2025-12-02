import asyncio
import logging

import random
from typing import Optional

from bot.db.db_dependency import DBDependency

from max.db.max_repo import MaxRepository

from .client import MaxClient

logger = logging.getLogger(__name__)


class MaxManager:
    """
    `MaxManager` объединяет несколько активных аккаунтов (сессий)
    и управляет ими, вызывая внутренние методы классов `MaxClient`,
    используя `key` (или Telegram ID владельца) в качестве ключа.

    Для работы класса необходимы некоторые действия, например, add_client().
    А если функционала недостаточно, то его легко дополнить на основе существующих методов.

    Управление классов, на данный момент осуществляется в основном через `message_handler.py`
    """

    def __init__(self, db_dependency: DBDependency):
        self.clients: dict[str, MaxClient] = {}
        self.db_dependency = db_dependency

    async def startup(self):
        """
        Load saved accounts,
        use their token and owner TG ID to connect several account's at once
        """

        await self._load_clients()

    async def shutdown(self):
        """
        Disconnect all active Client's
        """

        for client in self.clients.values():
            await client.disconnect()

    async def add_client(self, key: int, token: str, save_in_db=True) -> None:
        """
        Create a new MaxClient with the existing token and add it to the manager
        And save it to the Database
        The key is the User TG ID
        """

        if key in self.clients:
            raise ValueError("Client with this TG User ID already exists")

        client = MaxClient(token=token, tg_user_id=key)

        if save_in_db:
            async with self.db_dependency.db_session() as session:
                db = MaxRepository(session)

                c = await db.save_account(user_tg_id=key, token=token)

                if not c:
                    logger.error("Failed save Client to DB")
                    return

        await client.connect(auth_with_token=True)

        self.clients[key] = client

    async def start_auth(self, key: int, phone_number: str):
        """
        To get token you need to login. an sms acception will be sent to your phone
        The key is the User TG ID
        """

        if not phone_number or key is None:
            raise ValueError("Phone number and key are required")

        if key in self.clients:
            raise Exception("Client with this TG User ID already exists")

        client = MaxClient(tg_user_id=key)

        await client.connect(auth_with_token=False)
        await client.start_auth(phone_number)

        self.clients[key] = client

    async def check_code(self, key: int, short_token: str, code: str):
        """
        Verify code and get token
        The key is User TG ID
        """

        if not short_token or not code or key is None:
            raise ValueError("All fields are required")

        client = self.get_client(key)

        if client is None:
            raise ValueError("Client with this TG User ID doesn't exist")

        await client.check_code(short_token, code)

    async def get_messages_from_chat(self, key: int, chat_id: int):
        """
        Get messages from a specific chat for a user
        The key is User TG ID
        """

        client = self.get_client(key)

        if client is None:
            raise ValueError("Client with this TG User ID doesn't exist")

        await client.get_messages_from_chat(chat_id)

    async def subscribe_to_chat(self, key: int, chat_id: str):
        """
        Subscribe to a chat to listen for new messages
        The key is User TG ID
        """

        client = self.get_client(key)

        if client is None:
            raise ValueError("Client with this TG User ID doesn't exist")

        await client.listen_to_chat(chat_id)

    async def remove_client(self, key: int):
        """
        Remove a MaxClient from the parser
        The key is User TG ID
        """

        if key not in self.clients:
            raise ValueError("Client with this TG User ID doesn't exist")

        del self.clients[key]

    def get_client(self, key: int) -> Optional[MaxClient]:
        """
        Get a MaxClient by its TG User ID
        The key is User TG ID
        """

        if key not in self.clients:
            raise ValueError("Client with this TG User ID doesn't exist")

        return self.clients[key]

    async def _load_clients(self):
        """
        Load saved accounts,
        use their token and owner TG ID to connect several account's at once
        """

        accounts = []

        async with self.db_dependency.db_session() as session:
            db = MaxRepository(session)

            accounts = await db.get_all_accounts()

        if len(accounts) == 0:
            logger.info("No saved accounts")
            return

        for acc in accounts:
            # Add delay between connections to avoid rate limiting
            await asyncio.sleep(random.randint(1, 2))

            try:
                await self.add_client(acc.tg_id, acc.token, save_in_db=False)
            except Exception as e:
                logger.error(f"Failed to load account {acc.tg_id}: {e}")
                continue
