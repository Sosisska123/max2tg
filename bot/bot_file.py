from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# from aiogram.client.session.aiohttp import AiohttpSession

from settings import env

bot = Bot(
    token=env.bot_token.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

# PYTHONANYWHERE
# session = AiohttpSession(proxy="http://proxy.server:3128")

# bot = Bot(
#     token=config.bot_token.get_secret_value(),
#     default=DefaultBotProperties(parse_mode=ParseMode.HTML),
#     session=session,
# )
