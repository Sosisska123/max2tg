from asyncio import QueueShutDown
import logging
import re


from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.user_kb import create_max_availible_chats_keyboard
from utils.states import LoginWithMax, SubscribeMaxChat
from db.database import Database

from keyboards.user_kb import main_user_panel
from keyboards.setup_ui import set_bot_commands

from utils.phrases import ButtonPhrases, ErrorPhrases, Phrases
from parser.client import MaxParser

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def start_command(message: Message, db: Database) -> None:
    if not await db.get_user(message.from_user.id):
        await message.answer(Phrases.first_greeting())
    else:
        # Show keyboard only if chat is private

        if message.chat.type == "private":
            await message.answer(Phrases.start(), reply_markup=main_user_panel())
        else:
            await message.answer(Phrases.start())

        await set_bot_commands(message.bot)


@router.message(Command("reg"))
async def select_group(message: Message, command: CommandObject, db: Database) -> None:
    if await db.get_user(message.from_user.id):
        await message.answer(Phrases.already_registered())
        return

    try:
        if command.args.lower() in [
            "нпк",
            "кнн",
        ]:  # todo заменить на реал группы. когда нибудь
            await db.create_user(
                message.from_user.id,
                message.from_user.username,
                command.args.lower(),
            )

            # Show keyboard only if chat is private

            if message.chat.type == "private":
                await message.answer(Phrases.success(), reply_markup=main_user_panel())
            else:
                await message.answer(Phrases.success())

            logger.info("User %s registered", message.from_user.username)

            await set_bot_commands(message.bot)

        else:
            await message.answer(ErrorPhrases.group_not_found())
            return
    except TypeError as e:
        await message.reply(ErrorPhrases.invalid())
        logger.error(e)
        return
    except Exception as e:
        await message.reply(ErrorPhrases.something_went_wrong())
        logger.error(e)


# region MAX REGISTRATION


@router.message(
    Command(ButtonPhrases.command_activate_max),
    F.chat.type.in_(("group", "supergroup")),
)
async def admin_activate_max_command(
    message: Message, db: Database, state: FSMContext
) -> None:
    """
    Mark this group as connected to the MAX forwarding
    example: /max_subscribe
    """

    user = await db.get_user(message.from_user.id)

    # Check if user is registered
    if not user:
        await message.reply(ErrorPhrases.user_not_found())
        return

    # if user is not logged in with MAX phone number
    if not user.can_connect_max:
        await message.reply(Phrases.max_registration_required())
        return

    # Check if command has invoked in the correct chat type
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(ErrorPhrases.wrong_chat_type())
        return

    logger.debug(
        "CHAT ID %s | CHAT TYPE %s | CHAT NAME %s",
        message.chat.id,
        message.chat.type,
        message.chat.title,
    )

    # If this group is already connected we'll return
    group = await db.get_tg_group(message.chat.id)
    if group is not None:
        await message.answer(ErrorPhrases.chat_already_connected(group.title))
        return

    # Add new subscription
    group = await db.create_tg_group(
        group_id=message.chat.id, title=message.chat.title, creator_id=user.tg_id
    )

    if group:
        await message.answer(
            Phrases.group_connected_success(message.chat.title, group.created_user_id),
            reply_markup=create_max_availible_chats_keyboard(
                await db.get_list_max_available_chats()
            ),
        )
    else:
        await message.answer(ErrorPhrases.something_went_wrong())

    await state.set_state(SubscribeMaxChat.select_listening_chat)


@router.message(
    Command(ButtonPhrases.command_deactivate_max),
    F.chat.type.in_(("group", "supergroup")),
)
async def admin_deactivate_max_command(message: Message, db: Database) -> None:
    """
    Unmark this group as connected to the MAX forwarding
    example: /max_unsubscribe
    """

    # Check if command has invoked in the correct chat type
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(ErrorPhrases.wrong_chat_type())
        return

    logger.debug(
        "DEACTIVATE CHAT ID %s | CHAT TYPE %s | CHAT NAME %s",
        message.chat.id,
        message.chat.type,
        message.chat.title,
    )

    # If this group ain't subscribed we'll return
    group = await db.get_tg_group(message.chat.id)

    if group is None:
        await message.answer(ErrorPhrases.chat_never_connected(message.chat.title))
        return

    # Check that the same user wants to delete this group from subscription
    if user := await db.get_user(message.from_user.id):
        if group.created_user_id != user.tg_id:
            await message.answer(Phrases.max_same_user_error(group.created_user_id))
            return
    else:
        await message.answer(ErrorPhrases.user_not_found())
        return

    # unsubscribe Otherwise
    r = await db.remove_tg_group(group.group_id)

    if r:
        await message.answer(Phrases.group_disconnected_success(message.chat.title))
    else:
        await message.answer(ErrorPhrases.something_went_wrong())


@router.message(Command(ButtonPhrases.command_max_reg))
async def max_reg_command(message: Message, db: Database, state: FSMContext) -> None:
    # Check if user not registered
    user = await db.get_user(message.from_user.id)

    if not user:
        await message.answer(ErrorPhrases.user_not_found())
        return

    # Check if user already logged with Max phone number
    if user.can_connect_max:
        await message.answer(Phrases.max_already_logged())
        return

    await message.reply(Phrases.max_phone_number_request())

    await state.set_state(LoginWithMax.phone_number)


@router.message(LoginWithMax.phone_number)
async def max_phone_number(
    message: Message, state: FSMContext, parser: MaxParser
) -> None:
    try:
        if not message.text:
            raise ValueError("No text provided")

        phone_number = message.text

        # Format ph nm
        if not re.match(r"^\+7\d{10}$", phone_number):
            raise ValueError(
                f"Phone number must be in format +7xxxxxxxxxx, got: {phone_number}"
            )

        await parser.parser_queue.put(
            {
                "action": "start_auth",
                "user_id": message.from_user.id,
                "data": {"phone": phone_number},
            }
        )

    except ValueError:
        await message.reply(ErrorPhrases.invalid())
        await state.clear()
        return

    except QueueShutDown as e:
        logger.error("Failed to queue auth request: %s", e)
        await message.reply(ErrorPhrases.network_issues())
        await state.clear()
        return

    await message.reply(Phrases.max_wait_for_phone_acception(phone_number))
    await state.set_state(LoginWithMax.phone_code)


@router.message(LoginWithMax.phone_code)
async def max_phone_code(
    message: Message, db: Database, state: FSMContext, parser: MaxParser
) -> None:
    try:
        code = message.text

        if not code.isdigit():
            raise ValueError("Code must contain only digits")

        token = await db.get_max_token(message.from_user.id)

        if token is None:
            raise Exception("Token not found")

        await parser.parser_queue.put(
            {
                "action": "verify_code",
                "user_id": message.from_user.id,
                "data": {"code": code, "token": token},
            }
        )

        await message.reply(Phrases.wait_for_confirmation())

    except ValueError:
        await message.reply(ErrorPhrases.invalid())

    except QueueShutDown as e:
        logger.error("Failed to queue auth request: %s", e)
        await message.reply(ErrorPhrases.network_issues())

    except Exception as e:
        logger.error(e)
        await message.reply(ErrorPhrases.something_went_wrong())

    finally:
        await state.clear()
        return


@router.message(Command(ButtonPhrases.command_max_delete))
async def max_delete_command(message: Message, db: Database) -> None:
    pass


@router.message(Command(ButtonPhrases.command_max_help))
async def max_reg_help(message: Message) -> None:
    await message.answer(ButtonPhrases.max_reg_help())


# endregion
