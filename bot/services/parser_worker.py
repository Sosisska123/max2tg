import logging

from aiogram import Bot

from db.database import Database
from db.db_dependency import DBDependency
from utils.phrases import Phrases


logger = logging.getLogger(__name__)


async def listen_for_parser_messages(db_dependency: DBDependency, bot_queue, bot: Bot):
    while True:
        message = await bot_queue.get()

        try:
            action = message.get("action", None)
            user_id = message.get("user_id", None)
            data = message.get("data", {})

            match action:
                case "phone_confirmed":
                    token_value = data.get("token", None)

                    if not data:
                        logger.error("Missing data for send_short_token action")
                        continue

                    if not user_id or not token_value:
                        logger.error(
                            f"Missing user_id or token in send_short_token data: {data}"
                        )
                        continue

                    logger.info(
                        "📃 Phone number confirmed, waiting for sms code...| Token: %s | User ID: %s",
                        token_value,
                        user_id,
                    )

                    async with db_dependency.db_session() as session:
                        db = Database(session=session)

                        await db.update_user_max_token(user_id, token_value)
                        await db.update_user_max_permission(user_id, True)
                        await bot.send_message(user_id, Phrases.max_request_sms())

                case "sms_confirmed":
                    if not user_id:
                        logger.error(f"Missing user_id for {action} action")
                        continue

                    await bot.send_message(user_id, Phrases.max_login_success())

                case "fetch_chats":
                    all_message = data.get("all_message", None)

                    if not all_message:
                        logger.error(f"Missing all_message in fetch_chats data: {data}")
                        continue

                    logger.info(message)

                    async with db_dependency.db_session() as session:
                        db = Database(session=session)

                        for chat in all_message.get("payload", {}).get("chats", []):
                            chat_id = chat.get("id", None)
                            chat_title = chat.get("title", None)

                            if not chat_id or not chat_title:
                                continue

                            msgs_count = chat.get("messagesCount", None)
                            last_msg_id = chat.get("lastMessage").get("id", None)

                            await db.store_user_max_chat(
                                chat_id=chat_id,
                                chat_title=chat_title,
                                owner_tg_id=user_id,
                                messages_count=msgs_count,
                                last_message_id=last_msg_id,
                            )

                case "send_chat_list":
                    pass
                case _:
                    logger.error(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error while executing command from parser: {e}")

        finally:
            bot_queue.task_done()
