import logging
import asyncio

from bot.db.database import init_db
from bot.bot_file import bot
from bot.db.db_dependency import DBDependency
from bot.run_bot import start_bot

from core.message_handler import handle_from_bot, handle_from_ws

from max.clients_manager import MaxManager

from config import config


logging.basicConfig(
    level=logging.INFO,
    datefmt=config.logging.date_format,
    format=config.logging.log_format,
)


async def main():
    db_dependency = DBDependency(config=config)

    # Initialize database
    await init_db(db_dependency.engine)

    max_manager = MaxManager()

    logging.info("================ Бот запущен ================")

    await asyncio.gather(
        start_bot(config=config, db_dependency=db_dependency),
        handle_from_bot(bot=bot, db_dependency=db_dependency),
        handle_from_ws(max_manager=max_manager),
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("================ Бот остановлен ================")
    except Exception as e:
        logging.error(f"Ошибка {e}", exc_info=True)
