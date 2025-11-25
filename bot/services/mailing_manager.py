from typing import Union
import logging

from aiogram import Bot
from aiogram.utils.media_group import MediaGroupBuilder

from bot.db.database import Database
from bot.keyboards.admin.admin_kb import manage_new_schedule_inline_kb
from core.message_models import Attach
from bot.utils.phrases import ErrorPhrases, Phrases

from config import config

logger = logging.getLogger(__name__)


async def forward_message_to_group(
    bot: Bot,
    tg_group_ids: Union[int, list[int]],
    sender_name: str,
    max_chat: str,
    message_text: str = None,
    replied_sender_name: str = None,
    replied_text: str = None,
    medias: list[Attach] = None,
):
    """Forward a single message to numerous group.

    Args:
        bot (Bot): Bot object to perform sending
        tg_groups (list[str]): List of target subscribed groups ID's
        message_text (str): Source message text
        username (str): Sender username
        max_chat (str): Chat name
        replied_sender_name (str, optional): Replied sender name. Defaults to None.
        replied_text (str, optional): Replied text. Defaults to None.
        medias (list[MediaModel], optional): List of media to forward. Max up to 10. Defaults to None.
    """
    # if message has attached media

    if medias:
        # If media is in plural

        many_files = is_in_plural(medias)

        if many_files:
            media_group = MediaGroupBuilder(
                caption=Phrases.max_forwarded_message_template(
                    max_chat,
                    sender_name,
                    message_text,
                    replied_sender_name,
                    replied_text,
                )
            )

            max_files = min(len(medias), 10)

            for media in medias[:max_files]:
                match media.type:
                    case "photo":
                        media_group.add_photo(media.base_url)
                    case "doc":
                        media_group.add_document(media.base_url)
                    case "video":
                        media_group.add_video(media.base_url)
        else:
            # Otherwise if it has only one file

            # Assign the first object of this list to a single variable
            single_media = medias[0]

    if isinstance(tg_group_ids, int):
        tg_group_ids = [tg_group_ids]

    for group_id in tg_group_ids:
        if many_files:
            # Send media group with caption if its in plural

            await bot.send_media_group(
                chat_id=group_id,
                media=media_group.build(),
            )

        elif single_media:
            # Send single media with caption

            match single_media.type:
                case "photo":
                    await bot.send_photo(
                        chat_id=group_id,
                        photo=single_media.base_url,
                        caption=Phrases.max_forwarded_message_template(
                            max_chat,
                            sender_name,
                            message_text,
                            replied_sender_name,
                            replied_text,
                        ),
                    )

                case "doc":
                    await bot.send_document(
                        chat_id=group_id,
                        document=single_media.base_url,
                        caption=Phrases.max_forwarded_message_template(
                            max_chat,
                            sender_name,
                            message_text,
                            replied_sender_name,
                            replied_text,
                        ),
                    )

                case "video":
                    await bot.send_video(
                        chat_id=group_id,
                        video=single_media.base_url,
                        caption=Phrases.max_forwarded_message_template(
                            max_chat,
                            sender_name,
                            message_text,
                            replied_sender_name,
                            replied_text,
                        ),
                    )

        elif not many_files and not single_media:
            # Send text message otherwise

            await bot.send_message(
                chat_id=group_id,
                text=Phrases.max_forwarded_message_template(
                    max_chat,
                    sender_name,
                    message_text,
                    replied_sender_name,
                    replied_text,
                ),
            )

        else:
            logger.error(ErrorPhrases.something_went_wrong())


# region admin


async def send_new_post_to_admin(
    bot: Bot, group: str, file_type: str, files: list[str] | str, db: Database
):
    many_files = is_in_plural(files)

    # vremenno todo ⚠️⚠️⚠️
    if file_type == "photo":
        # 5 - vmeste s ring schedyle:: ring | 1 course | 2c | 3c | ...
        if len(files) == 5:
            files = files[2]
            many_files = False

        elif many_files:
            files = files[1]  # 1 - второй по счету т.е. 2 курс
            many_files = False

        elif many_files:  # пока что так, чтобы ничего не ломалось
            files = files[0]
            many_files = False

    try:
        temp_schedule = await db.save_temp_schedule(group, file_type, files)

        if not temp_schedule:
            logger.error(ErrorPhrases.something_went_wrong())
            return

        temp_schedule_id = temp_schedule.id
    except Exception as e:
        logger.error(f"Error saving temp schedule: {e}")
        return

    if many_files:
        media_group = MediaGroupBuilder(caption=group)
        add_media = (
            media_group.add_document if file_type == "doc" else media_group.add_photo
        )
        for file in files:
            add_media(file)

    from utils.scheduler import create_job

    for admin in config.bot.admins:
        if many_files:
            msg = await bot.send_media_group(admin, media_group.build())

            await bot.send_message(
                chat_id=admin,
                text=group,
                reply_markup=manage_new_schedule_inline_kb(temp_schedule_id),
            )

            create_job(bot, db, temp_schedule_id, msg)

            return

        if file_type == "doc":
            msg = await bot.send_document(
                caption=group,
                chat_id=admin,
                document=files,
                reply_markup=manage_new_schedule_inline_kb(temp_schedule_id),
            )

            create_job(bot, db, temp_schedule_id, msg)

        elif file_type == "photo":
            msg = await bot.send_photo(
                caption=group,
                chat_id=admin,
                photo=files,
                reply_markup=manage_new_schedule_inline_kb(temp_schedule_id),
            )

            create_job(bot, db, temp_schedule_id, msg)


def is_in_plural(files: list[str]) -> bool:
    if isinstance(files, str):
        return False

    elif isinstance(files, list) and len(files) == 1:
        return False

    return len(files) > 1


# endregion
