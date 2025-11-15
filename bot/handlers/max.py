import re
import logging

from asyncio import QueueShutDown

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.keyboards.user_kb import max_available_chats_inline_kb

from bot.utils.states import LoginWithMax, SubscribeMaxChat
from bot.utils.phrases import ButtonPhrases, ErrorPhrases, Phrases

from bot.db.database import Database

from core.queue_manager import queue_manager
from core.message_models import StartAuthMessage, VerifyCodeMessage


logger = logging.getLogger(__name__)
router = Router()


@router.message(Command(ButtonPhrases.command_activate_max))
async def subscribe_max(message: Message, db: Database, state: FSMContext) -> None:
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
        "MAX_SUBSCRIBE | CHAT ID %s | CHAT TYPE %s | CHAT NAME %s",
        message.chat.id,
        message.chat.type,
        message.chat.title,
    )

    # If this group is already connected we'll return
    group = await db.get_tg_group_by_id(message.chat.id)
    if group is not None:
        await message.answer(ErrorPhrases.chat_already_connected(group.group_title))
        return

    # Add new subscription
    group = await db.store_tg_group(
        group_id=message.chat.id, title=message.chat.title, creator_id=user.tg_id
    )

    if group:
        await message.answer(
            Phrases.group_connected_success(message.chat.title, group.creator_id),
            reply_markup=max_available_chats_inline_kb(
                await db.get_max_available_chats(user.tg_id)
            ),
        )
    else:
        await message.answer(ErrorPhrases.something_went_wrong())

    await state.set_state(SubscribeMaxChat.select_listening_chat)


@router.message(Command(ButtonPhrases.command_deactivate_max))
async def unsubscribe_max(message: Message, db: Database) -> None:
    """
    Unmark this group as connected to the MAX forwarding
    example: /max_unsubscribe
    """

    # Check if command has invoked in the correct chat type
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(ErrorPhrases.wrong_chat_type())
        return

    logger.debug(
        "UNSUBSCRIBE MAX | CHAT ID %s | CHAT TYPE %s | CHAT NAME %s",
        message.chat.id,
        message.chat.type,
        message.chat.title,
    )

    group = await db.get_tg_group_by_id(message.chat.id)

    # If this group ain't subscribed we'll return
    if group is None:
        await message.answer(ErrorPhrases.chat_never_connected(message.chat.title))
        return

    user = await db.get_user(message.from_user.id)

    # Check that the same user wants to delete this group from subscription
    if user:
        if group.creator_id != user.tg_id:
            await message.answer(Phrases.max_same_user_error(group.creator_id))
            return
    else:
        await message.answer(ErrorPhrases.user_not_found())
        return

    # unsubscribe
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
async def max_phone_number(message: Message, state: FSMContext) -> None:
    try:
        if not message.text:
            raise ValueError("No text provided")

        phone_number = message.text

        # Format ph nm
        if not re.match(r"^\+7\d{10}$", phone_number):
            raise ValueError(
                f"Phone number must be in format +7xxxxxxxxxx, got: {phone_number}"
            )

        # Send message
        data = StartAuthMessage(user_id=message.from_user.id, phone=phone_number)
        await queue_manager.to_ws.put(data)

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
async def max_phone_code(message: Message, db: Database, state: FSMContext) -> None:
    try:
        code = message.text

        if not code.isdigit():
            raise ValueError("Code must contain only digits")

        token = await db.get_max_token(message.from_user.id)

        if token is None:
            raise Exception("Token not found")

        data = VerifyCodeMessage(user_id=message.from_user.id, code=code, token=token)
        await queue_manager.to_ws.put(data)

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
async def max_delete_command(message: Message) -> None:
    await message.answer("not implemented yet")


@router.message(Command(ButtonPhrases.command_max_help))
async def max_reg_help(message: Message) -> None:
    await message.answer(ButtonPhrases.max_reg_help())
