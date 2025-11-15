from aiogram import Dispatcher

from bot.callbacks.user import router as user_callback_router

from bot.handlers.admin.admin_handlers import router as admin_router
from bot.handlers.user import router as user_router
from bot.handlers.max import router as max_router

from bot.db.db_dependency import DBDependency

from bot.middlewares.throttling import ThrottlingMiddleware

from bot.bot_file import bot
from config import Settings

dp = Dispatcher()


async def start_bot(config: Settings, db_dependency: DBDependency) -> None:
    # Initialize database dependency
    async_session = db_dependency.db_session

    dp.include_routers(
        admin_router,
        user_router,
        max_router,
        user_callback_router,
    )

    # Add throttling middleware after registration middleware
    dp.message.middleware(ThrottlingMiddleware(session=async_session, config=config))
    dp.callback_query.middleware(
        ThrottlingMiddleware(session=async_session, config=config)
    )

    await bot.delete_webhook(True)
    await dp.start_polling(bot)
