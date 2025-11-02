from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
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
