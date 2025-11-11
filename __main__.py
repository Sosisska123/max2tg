import logging
import asyncio

from bot.run_bot import start
from settings import config


logging.basicConfig(
    level=logging.INFO,
    datefmt=config.logging.date_format,
    format=config.logging.log_format,
)

if __name__ == "__main__":
    try:
        logging.info("================ Бот запущен ================")
        asyncio.gather(start())

    except KeyboardInterrupt:
        logging.info("================ Бот остановлен ================")

    except Exception as e:
        logging.error(f"Ошибка {e}", exc_info=True)
