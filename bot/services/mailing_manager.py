from typing import Union
import logging

from aiogram import Bot
from aiogram.utils.media_group import MediaGroupBuilder

from core.message_models import Attach
from bot.utils.phrases import ErrorPhrases, Phrases

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


def is_in_plural(files: list[str]) -> bool:
    if isinstance(files, str):
        return False

    elif isinstance(files, list) and len(files) == 1:
        return False

    return len(files) > 1


# endregion
