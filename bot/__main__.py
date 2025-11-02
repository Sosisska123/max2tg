import asyncio
import logging

from aiogram import Dispatcher

from handlers.admin.admin_handlers import router as admin_router
from handlers.user import router as user_router
from handlers.group import router as group_router

# from callbacks.defaults import router as default_callback_router

from db.database import init_db
from db.db_dependency import DBDependency

from middlewares.throttling import ThrottlingMiddleware

from bot_file import bot
from settings import config


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

    # Initialize database
    await init_db(db_dependency._engine)

    dp.include_routers(
        admin_router,
        user_router,
        group_router,
        # default_callback_router,
    )

    # Add throttling middleware after registration middleware
    dp.message.middleware(
        ThrottlingMiddleware(session=async_session, ttl=config.ttl_default)
    )
    dp.callback_query.middleware(
        ThrottlingMiddleware(session=async_session, ttl=config.ttl_default)
    )

    # vk_schedule.create_scheduler(
    #     npk_vk_requests, knn_vk_requests, db_dependency=db_dependency
    # )

    await bot.delete_webhook(True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        logging.info("================ Бот запущен ================")
        asyncio.run(start())
    except KeyboardInterrupt:
        # scheduler.shutdown()
        # await bot.session.close()
        logging.info("================ Бот остановлен ================")

    except Exception as e:
        logging.error(f"Ошибка {e}", exc_info=True)
