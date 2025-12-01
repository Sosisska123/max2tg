from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.utils.phrases import ButtonPhrases


def reply_startup_kb() -> ReplyKeyboardMarkup:
    buttons = [
        [
            KeyboardButton(text=ButtonPhrases.today_command_panel),
            KeyboardButton(text=ButtonPhrases.lessons_command_panel),
        ],
        [
            KeyboardButton(text=ButtonPhrases.settings_command_panel),
            KeyboardButton(text=ButtonPhrases.rings_command_panel),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def under_post_inline_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text=ButtonPhrases.turn_off_notifications_command,
        callback_data=ButtonPhrases.turn_off_notifications_command,
    )

    builder.button(
        text=ButtonPhrases.rings_command_panel,
        callback_data=ButtonPhrases.rings_command_panel,
    )
    return builder.adjust(2).as_markup(resize_keyboard=True)
