import logging

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from max.models.groups import Chat


def max_chats_inline_kb(chats: list[Chat]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if len(chats) == 0:
        builder.button(text="🚫 Пусто", callback_data="max_chat_empty")
        return builder.as_markup(resize_keyboard=True)
        # ༒︎✟ϟϟ⌖𐀏

    try:
        for chat in chats:
            builder.button(
                text=chat.chat_title, callback_data=f"max_chat_{chat.chat_id}"
            )

        builder.button(text="☁️ Любой", callback_data="max_chat_any")
    except AttributeError as e:
        logging.error(f"Error accessing chat attributes: {e}", exc_info=True)
        builder = InlineKeyboardBuilder()
        builder.button(text="🚫 Пусто", callback_data="max_chat_empty")
        return builder.as_markup(resize_keyboard=True)
    except Exception as e:
        logging.error(f"Error creating keyboard: {e}", exc_info=True)
        builder = InlineKeyboardBuilder()
        builder.button(text="🚫 Пусто", callback_data="max_chat_empty")
        return builder.as_markup(resize_keyboard=True)

    return builder.adjust(2, repeat=True).as_markup(resize_keyboard=True)
