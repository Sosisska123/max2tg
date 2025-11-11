import logging
from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.max_group import MaxGroupConfig
from utils.phrases import ButtonPhrases


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


def max_available_chats_inline_kb(groups: list[MaxGroupConfig]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if len(groups) == 0:
        builder.button(text="🚫 Empty", callback_data="max_chat_empty")
        return builder.as_markup(resize_keyboard=True)
        # ༒︎✟ϟϟ⌖𐀏

    try:
        for group in groups:
            builder.button(
                text=group.chat_title, callback_data=f"max_chat_{group.chat_id}"
            )
    except Exception as e:
        logging.error(e)
        builder.button(text="🚫 Empty", callback_data="max_chat_empty")
        return builder.as_markup(resize_keyboard=True)

    return builder.adjust(2, repeat=True).as_markup(resize_keyboard=True)
