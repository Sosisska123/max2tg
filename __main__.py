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

    tasks = [
        asyncio.create_task(start_bot(config=config, db_dependency=db_dependency)),
        asyncio.create_task(handle_from_bot(max_manager=max_manager)),
        asyncio.create_task(handle_from_ws(bot=bot, db_dependency=db_dependency)),
    ]

    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        logging.error(f"Task failed: {e}", exc_info=True)
    finally:
        # Cancel all running tasks
        for task in tasks:
            if not task.done():
                task.cancel()

    # Wait for cancellation to complete
    await asyncio.gather(*tasks, return_exceptions=True)

    # Cleanup resources
    await db_dependency.engine.dispose()
    # Add any other cleanup for max_manager or bot if needed


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("================ Бот остановлен ================")
    except Exception as e:
        logging.error(f"Ошибка {e}", exc_info=True)
