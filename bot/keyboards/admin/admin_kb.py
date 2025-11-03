from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from models.max_groups import GGroup

from utils.phrases import AdminPhrases


def main_admin_panel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=AdminPhrases.check_npk_command,
                    callback_data=AdminPhrases.check_npk_command,
                ),
                InlineKeyboardButton(
                    text=AdminPhrases.check_knn_command,
                    callback_data=AdminPhrases.check_knn_command,
                ),
            ],
            [
                InlineKeyboardButton(
                    text=AdminPhrases.load_schedule_command,
                    callback_data=AdminPhrases.load_schedule_command,
                ),
            ],
        ]
    )


def manage_new_schedule(temp_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(
        text=AdminPhrases.approve_schdule_command,
        callback_data=f"{AdminPhrases.approve_schdule_command}:{temp_id}",
    )
    builder.button(
        text=AdminPhrases.approve_schdule_no_sound_command,
        callback_data=f"{AdminPhrases.approve_schdule_no_sound_command}:{temp_id}",
    )

    builder.button(
        text=AdminPhrases.reject_schdule_command,
        callback_data=f"{AdminPhrases.reject_schdule_command}:{temp_id}",
    )

    builder.button(
        text=AdminPhrases.edit_schdule_command,
        callback_data=f"{AdminPhrases.edit_schdule_command}:{temp_id}",
    )

    return builder.adjust(2).as_markup(resize_keyboard=True)


def create_max_chats_keyboard(*groups: GGroup) -> InlineKeyboardMarkup:
    ggroups = list(groups)
    builder = InlineKeyboardBuilder()

    if len(ggroups) == 0:
        builder.button(text="🚫 Empty", callback_data="max_chat_empty")
        return builder.as_markup(resize_keyboard=True)
        # ༒︎✟ϟϟ⌖𐀏

    for group in ggroups:
        builder.button(text=group.title, callback_data=f"max_chat_{group.id}")

    return builder.adjust(2, repeat=True).as_markup(resize_keyboard=True)
