from aiogram import F, Router
from aiogram.filters import Command

from aiogram.types import Message

from db.database import Database

from keyboards.setup_ui import set_bot_commands
from utils.phrases import AdminPhrases, Phrases

router = Router()
