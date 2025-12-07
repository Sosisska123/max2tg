import re
import logging

from asyncio import QueueShutDown

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.utils.states import LoginWithMax
from bot.utils.phrases import ButtonPhrases, ErrorPhrases, Phrases

from bot.db.database import Database

from core.queue_manager import get_queue_manager
from core.message_models import StartAuthMessage, VerifyCodeMessage, SubscribeGroupDTO


logger = logging.getLogger(__name__)
router = Router()


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
async def max_phone_number(message: Message, state: FSMContext) -> None:
    try:
        if not message.text:
            raise ValueError("No text provided")

        phone_number = message.text

        # Format ph nm
        if not (
            re.match(r"^\+7\d{10}$", phone_number)
            or re.match(r"^7\d{10}$", phone_number)
        ):
            raise ValueError("Phone number must be in format +7xxxxxxxxxx")

        if re.match(r"^7\d{10}$", phone_number):
            phone_number = f"+{phone_number}"

        # Send message
        data = StartAuthMessage(user_id=message.from_user.id, phone=phone_number)
        await get_queue_manager().to_ws.put(data)

    except ValueError as e:
        logger.error("Invalid phone number: %s. %s", message.text, e)
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
async def max_phone_code(message: Message, state: FSMContext) -> None:
    try:
        code = message.text

        if not code.isdigit():
            raise ValueError("Code must contain only digits")

        data = VerifyCodeMessage(user_id=message.from_user.id, code=code)
        await get_queue_manager().to_ws.put(data)

        await message.reply(Phrases.wait_for_confirmation())

    except ValueError as e:
        logger.error("Invalid code: %s. %s", message.text, e)
        await message.reply(ErrorPhrases.invalid())

    except QueueShutDown as e:
        logger.error("Failed to queue auth request: %s", e)
        await message.reply(ErrorPhrases.network_issues())

    except Exception as e:
        logger.error(e)
        await message.reply(ErrorPhrases.something_went_wrong())

    finally:
        await state.clear()


@router.message(Command(ButtonPhrases.command_max_delete))
async def max_delete_command(message: Message) -> None:
    await message.answer("not implemented yet")


@router.message(Command(ButtonPhrases.command_max_help))
async def max_reg_help(message: Message) -> None:
    await message.answer(ButtonPhrases.max_reg_help())


@router.message(Command(ButtonPhrases.command_subscribe_max))
async def subscribe_max(message: Message, db: Database) -> None:
    """
    Subscribe this group to MAX chat updates
    """

    logger.debug(
        "MAX_SUBSCRIBE | CHAT ID %s | CHAT TYPE %s | CHAT NAME %s | USER ID %s",
        message.chat.id,
        message.chat.type,
        message.chat.title,
        message.from_user.id,
    )

    user = await db.get_user(message.from_user.id)

    # Check if user is registered
    if not user:
        await message.reply(ErrorPhrases.user_not_found())
        return

    # if user is not logged in with MAX phone number
    if not user.can_connect_max:
        await message.reply(Phrases.max_registration_required())
        return

    await get_queue_manager().to_ws.put(
        SubscribeGroupDTO(
            owner_id=user.tg_id,
            group_id=message.chat.id,
            group_title=message.chat.title or "N/A",
        )
    )


@router.message(Command(ButtonPhrases.command_unsubscribe_max))
async def unsubscribe_max(message: Message, db: Database) -> None:
    """
    Unmark this group as connected to the MAX forwarding
    example: /max_unsubscribe
    """

    logger.debug(
        "UNSUBSCRIBE MAX | CHAT ID %s | CHAT TYPE %s | CHAT NAME %s | USER ID %s",
        message.chat.id,
        message.chat.type,
        message.chat.title,
        message.from_user.id,
    )

    user = await db.get_user(message.from_user.id)

    # Check if user is registered
    if not user:
        await message.reply(ErrorPhrases.user_not_found())
        return

    try:
        await get_queue_manager().to_ws.put(
            SubscribeGroupDTO(
                type="unsub_group",
                owner_id=user.tg_id,
                group_id=message.chat.id,
                group_title=message.chat.title or "N/A",
            )
        )
        await message.reply(Phrases.max_chat_disconnection_success())
    except QueueShutDown as e:
        logger.error("Failed to queue unsubscribe request: %s", e)
        await message.reply(ErrorPhrases.network_issues())
    except Exception as e:
        logger.error("Failed to unsubscribe group: %s", e)
        await message.reply(ErrorPhrases.something_went_wrong())
