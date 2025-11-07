from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.max_groups import MAXGroup
from utils.phrases import ButtonPhrases


def main_user_panel() -> ReplyKeyboardMarkup:
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


def under_post_keyboard() -> InlineKeyboardMarkup:
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


def create_max_availible_chats_keyboard(*groups: MAXGroup) -> InlineKeyboardMarkup:
    ggroups = list(groups)
    builder = InlineKeyboardBuilder()

    if len(ggroups) == 0:
        builder.button(text="🚫 Empty", callback_data="max_chat_empty")
        return builder.as_markup(resize_keyboard=True)
        # ༒︎✟ϟϟ⌖𐀏

    for group in ggroups:
        builder.button(text=group.title, callback_data=f"max_chat_{group.id}")

    return builder.adjust(2, repeat=True).as_markup(resize_keyboard=True)


# def create_reply_keyboard(*buttons: str, sizes: tuple[int] = (2,)) -> ReplyKeyboardMarkup:
#     keyboard = ReplyKeyboardBuilder()

#     for text in buttons:
#         keyboard.add(KeyboardButton(text=text))

#     return keyboard.adjust(*sizes).as_markup(
#         resize_keyboard=True, one_time_keyboard=True
#     )
