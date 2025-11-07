import asyncio
import logging

from aiogram import Dispatcher

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from parser.client import MaxParser

from handlers.admin.admin_handlers import router as admin_router
from handlers.user import router as user_router
from handlers.group import router as group_router

from db.database import init_db
from db.db_dependency import DBDependency

from middlewares.throttling import ThrottlingMiddleware

from bot_file import bot
from settings import config
from services.parser_worker import listen_for_parser_messages

dp = Dispatcher()


logging.basicConfig(
    level=logging.INFO,
    datefmt=config.logging.date_format,
    format=config.logging.log_format,
)


async def start() -> None:
    # Initialize database dependency
    db_dependency = DBDependency()
    async_session = db_dependency.db_session

    # Initialize queues for bot-parser communication
    bot_queue = asyncio.Queue()

    # Initialize MaxParser
    parser = MaxParser(bot_queue)

    # Initialize database
    await init_db(db_dependency._engine)

    dp.include_routers(
        admin_router,
        user_router,
        group_router,
    )

    # Add throttling middleware after registration middleware
    dp.message.middleware(
        ThrottlingMiddleware(session=async_session, ttl=config.bot.ttl_default)
    )
    dp.callback_query.middleware(
        ThrottlingMiddleware(session=async_session, ttl=config.bot.ttl_default)
    )

    # Create a task to listen for commands from the bot
    asyncio.create_task(parser.listen_for_commands())

    asyncio.create_task(listen_for_parser_messages(db_dependency, bot_queue, bot))

    await bot.delete_webhook(True)
    await dp.start_polling(bot, parser=parser)


if __name__ == "__main__":
    try:
        logging.info("================ Бот запущен ================")
        asyncio.run(start())
    except KeyboardInterrupt:
        logging.info("================ Бот остановлен ================")

    except Exception as e:
        logging.error(f"Ошибка {e}", exc_info=True)
