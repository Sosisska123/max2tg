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
            action = message.get("action")
            token = message.get("token")
            data = message.get("data")

            match action:
                case "send_short_token":
                    async with db_dependency.session() as session:
                        db = Database(session=session)

                        await db.update_user_max_token(
                            data.get("user_id"), data.get("token")
                        )
                        await bot.send_message(
                            data.get("user_id"), Phrases.max_login_success()
                        )

                case "send_full_token":
                    pass

                case "send_chat_list":
                    pass

        except Exception as e:
            logger.error(f"Error while executing command from parser: {e}")

        finally:
            bot_queue.task_done()
