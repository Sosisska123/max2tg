import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from db.database import Database

from filters.is_admin import IsAdmin
from keyboards.admin.admin_kb import main_admin_panel

from models.schedule import ScheduleType
from models.temp_prikol import prikol

from utils.date_utils import get_tomorrow_date
from services.mailing_manager import send_new_post_to_admin, send_files_to_users
from utils.phrases import AdminPhrases, ErrorPhrases
from utils.states import LoadScheduleFsm

# from vk.vk_schedule import stop_parsing_jobs

from services.schedule import save_ring_schedule


router = Router()
logger = logging.getLogger(__name__)


# create admin menu, command variant
@router.message(Command("admin"), IsAdmin())
async def admin_panel_command(message: Message) -> None:
    await message.reply(
        AdminPhrases.admin_panel,
        reply_markup=main_admin_panel(),
    )


# region LOAD SCHEDULE


@router.message(Command(AdminPhrases.command_add_schedule), IsAdmin())
@router.message(
    F.text.startswith(AdminPhrases.load_schedule_command),
    IsAdmin(),
)
async def load_schedule_select_group_command(
    message: Message, state: FSMContext, command: CommandObject
):
    await state.set_state(LoadScheduleFsm.load_file)

    args = command.args.split()

    group = args[0].lower()
    load_type = args[1].lower()

    if group not in ["нпк", "кнн"]:
        await message.answer(ErrorPhrases.group_not_found())
        return

    await message.answer(AdminPhrases.load_schedule_text())

    await state.update_data(group=group)
    await state.update_data(type=load_type)


@router.message(
    IsAdmin(),
    LoadScheduleFsm.load_file,
)
async def load_schedule_load_file(message: Message, db: Database, state: FSMContext):
    data = await state.get_data()

    group = data.get("group")
    type = data.get("type")

    if type == "file":
        # TEMPORARY UNAVAIBLE
        await message.reply("⚠️ TEMPORARY UNAVAIBLE try URL instead")
        await state.clear()
        return

        if group == "нпк" and message.photo is not None:
            files = message.photo
            file_type = "photo"

        elif group == "кнн" and message.document is not None:
            files = message.document
            file_type = "doc"

        else:
            await message.reply(ErrorPhrases.wrong_file_type())
            await state.clear()
            return
    else:
        files = message.text
        file_type = "photo" if group == "нпк" else "doc"

    await state.clear()

    await send_new_post_to_admin(
        bot=message.bot,
        group=group,
        file_type=file_type,
        files=files,
        db=db,
    )


# endregion


# region ADD RING SCHEDULE


@router.message(Command(AdminPhrases.command_add_ring_schedule), IsAdmin())
async def admin_add_ring_schedule_command(
    message: Message, state: FSMContext, command: CommandObject
) -> None:
    """
    Manually add new (or update existing) ring schedule
    example: /add_ring_schedule [нпк/кнн] [file/url] [reg/def]
    """

    if len(command.args.split()) != 3:
        await message.reply(ErrorPhrases.length_error())
        return

    await state.set_state(LoadScheduleFsm.load_rings)
    # todo group, load_type check

    args = command.args.split()

    sch_type = args[2].lower()

    await state.update_data(sch_type=sch_type)

    await message.answer(AdminPhrases.load_schedule_text())


@router.message(
    IsAdmin(),
    LoadScheduleFsm.load_rings,
)
async def admin_add_ring_schedule_load_command(
    message: Message, db: Database, state: FSMContext
) -> None:
    url = message.text
    data = await state.get_data()
    sch_type = data.get("sch_type")

    if sch_type == "def":
        await save_ring_schedule(
            db, "нпк", get_tomorrow_date(), url, ScheduleType.DEFAULT_RING.value
        )

    elif sch_type == "reg":
        await save_ring_schedule(db, "нпк", get_tomorrow_date(), url)

    else:
        await message.reply(ErrorPhrases.invalid(), reply_markup=main_admin_panel())
        return

    await message.answer("✅ rings schedule added", reply_markup=main_admin_panel())
    await state.clear()


# endregion


@router.message(Command(AdminPhrases.command_prikol), IsAdmin())
async def admin_prikol_command(message: Message) -> None:
    """
    Make a sending schedule paid
    """

    prikol.is_prikol_activated = not prikol.is_prikol_activated

    if prikol.is_prikol_activated:
        await message.answer("✅ Prikol activated")
    else:
        await message.answer("❌ Prikol deactivated")


@router.message(Command(AdminPhrases.command_mail_everyone), IsAdmin())
async def admin_mail_everyone_command(
    message: Message,
    command: CommandObject,
    db: Database,
) -> None:
    """
    Send message to all users in a certain group
    example: /mail [message] [group] [ignore notification / Optional]
    """

    args = command.args.split()

    if len(args) < 2:
        await message.reply(ErrorPhrases.length_error())
        return

    (
        msg,
        group,
    ) = (
        args[0],
        args[1],
    )

    ignore_notification = args[2] if len(args) > 2 else False

    await send_files_to_users(
        message=msg,
        bot=message.bot,
        users=await db.get_all_users_in_group(group, ignore_notification),
    )


@router.message(Command(AdminPhrases.command_list_var), IsAdmin())
async def admin_var_list_command(message: Message) -> None:
    pass


@router.message(Command(AdminPhrases.command_set_var), IsAdmin())
async def admin_set_var_command(message: Message) -> None:
    pass


# @router.message(Command(AdminPhrases.command_clear_jobs), IsAdmin())
# async def admin_clear_jobs_command(message: Message) -> None:
#     """
#     Clear all jobs
#     """

#     stop_parsing_jobs()

#     await message.answer("✅ jobs cleared")


@router.message(Command(AdminPhrases.command_list), IsAdmin())
async def admin_list_command(message: Message) -> None:
    """
    List all available commands
    """
    await message.reply(AdminPhrases.comands_list())


@router.message(Command(AdminPhrases.command_add_user), IsAdmin())
async def admin_add_user_command(
    message: Message,
    command: CommandObject,
    db: Database,
) -> None:
    """
    Add user if it doesn't
    example: /add_user [ID] [GROUP] [username]
    """

    args = command.args.split()

    if len(args) != 2:
        await message.reply(ErrorPhrases.length_error())
        return

    try:
        await db.create_user(
            args[0].lower(),
            args[2],
            args[1].lower(),
        )
        await message.answer(
            "✅ User successfully added", reply_markup=main_admin_panel()
        )

    except TypeError as e:
        await message.reply(ErrorPhrases.invalid())
        logger.error(e)
        return


# region MAX


@router.message(Command(AdminPhrases.command_list_subscribed_groups_max), IsAdmin())
async def admin_max_subscribed_groups_max_command(
    message: Message, db: Database
) -> None:
    """
    List all subscribed Telegram groups
    """

    groups = await db.get_connected_groups_list()

    if groups is None:
        await message.answer(ErrorPhrases.something_went_wrong())
        return

    output = "\n".join(
        f"{group.title}: {group.group_link} | {group.tg_id}" for group in groups
    )
    await message.answer(output if output else "No subscribed groups found.")


# endregion
