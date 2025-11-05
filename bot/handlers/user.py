import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from keyboards.admin.admin_kb import create_max_chats_keyboard
from utils.states import LoginWithMax, SubscribeMaxChat
from db.database import Database

from keyboards.user_kb import main_user_panel
from keyboards.setup_ui import set_bot_commands

from utils.phrases import ButtonPhrases, ErrorPhrases, Phrases

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
    if not user.can_subscribe_max:
        await message.reply(Phrases.max_registration_required())
        return

    # Check if command has invoked in the correct chat type
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(ErrorPhrases.wrong_chat_type())
        return

    logging.debug(
        "CHAT ID %s | CHAT TYPE %s | CHAT NAME %s",
        message.chat.id,
        message.chat.type,
        message.chat.title,
    )

    # If this group is already connected we'll return
    group = await db.get_connected_group(message.chat.id)
    if group is not None:
        await message.answer(ErrorPhrases.chat_already_connected(group.title))
        return

    # Add new subscription
    group = await db.add_connected_group(
        tg_id=message.chat.id, title=message.chat.title, creator_id=user.tg_id
    )

    if group:
        await message.answer(
            Phrases.group_connected_success(message.chat.title, group.created_user_id),
            reply_markup=create_max_chats_keyboard(await db.max_get_avaible_chats()),
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

    logging.debug(
        "DEACTIVATE CHAT ID %s | CHAT TYPE %s | CHAT NAME %s",
        message.chat.id,
        message.chat.type,
        message.chat.title,
    )

    # If this group ain't subscribed we'll return
    group = await db.get_connected_group(message.chat.id)

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
    r = await db.remove_connected_group(group.group_link)

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
    if user.can_subscribe_max:
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
        if len(phone_number) == 12 and phone_number.startswith("+7"):
            phone_number = phone_number[2:]
        elif len(phone_number) == 11 and phone_number.startswith("7"):
            phone_number = phone_number[1:]
        elif len(phone_number) == 10:
            pass
        else:
            raise ValueError("Invalid phone number format")
        # Validate that phone_number contains only digits
        if not phone_number.isdigit():
            raise ValueError("Phone number must contain only digits")

    except ValueError:
        await message.reply(ErrorPhrases.invalid())
        await state.clear()
        return

    await message.reply(Phrases.max_phone_code_request(phone_number))

    await state.update_data(phone_number=phone_number)

    await state.set_state(LoginWithMax.phone_code)


@router.message(LoginWithMax.phone_code)
async def max_phone_code(message: Message, db: Database, state: FSMContext) -> None:
    data = await state.get_data()

    try:
        phone_number = data.get("phone_number")
        code = int(message.text)

    except ValueError:
        await message.reply(ErrorPhrases.invalid())
        await state.clear()
        return

    # TODO MAX LOGIN
    # TODO MAX LOGIN
    # TODO MAX LOGIN

    await db.update_user_max_state(message.from_user.id, True)

    await message.answer(Phrases.max_login_success())

    await state.clear()

    # Verify code with MAX API
    # is_verified = await verify_max_code(phone_number, code)

    # if is_verified:
    #     await db.update_user_max_state(message.from_user.id, True)
    #     await message.answer(Phrases.max_login_success())
    #     await state.clear()
    # else:
    #     await message.reply(ErrorPhrases.invalid_verification_code())
    #     await state.clear()


@router.message(Command(ButtonPhrases.command_max_delete))
async def max_delete_command(message: Message, db: Database) -> None:
    pass


@router.message(Command(ButtonPhrases.command_max_help))
async def max_reg_help(message: Message) -> None:
    await message.answer(ButtonPhrases.max_reg_help())


# endregion
