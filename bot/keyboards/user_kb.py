from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

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


# def creste_inline_keyboard(
#     *buttons: HomeworkData
# ) -> InlineKeyboardMarkup:
#     builder = InlineKeyboardBuilder()

#     for hw in buttons:
#         builder.button(
#             text=hw.lesson_name.capitalize()
#             if not hw.is_pinned
#             else f"{hw.lesson_name.capitalize()} [📌]",
#             callback_data=HomeworkCallbackData(
#                 action=action or "", lesson_name=hw.lesson_name, sharaga_type=hw.sharaga
#             ).pack(),
#         )

#     return builder.adjust(2, repeat=True).as_markup(resize_keyboard=True)


# def create_reply_keyboard(*buttons: str, sizes: tuple[int] = (2,)) -> ReplyKeyboardMarkup:
#     keyboard = ReplyKeyboardBuilder()

#     for text in buttons:
#         keyboard.add(KeyboardButton(text=text))

#     return keyboard.adjust(*sizes).as_markup(
#         resize_keyboard=True, one_time_keyboard=True
#     )
