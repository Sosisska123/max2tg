from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeAllGroupChats,
)

from utils.phrases import ButtonPhrases


async def set_bot_commands(bot: Bot):
    # UI Commands for private chats
    private_commands = [
        BotCommand(
            command=ButtonPhrases.lessons_command,
            description=ButtonPhrases.lessons_command_desc,
        ),
        BotCommand(
            command=ButtonPhrases.today_command,
            description=ButtonPhrases.today_command_desc,
        ),
        BotCommand(
            command=ButtonPhrases.homework_command,
            description=ButtonPhrases.homework_command_desc,
        ),
    ]

    # UI Commands for groups
    group_commands = [
        BotCommand(
            command=ButtonPhrases.command_activate_max,
            description=ButtonPhrases.command_activate_max_desc,
        ),
        BotCommand(
            command=ButtonPhrases.command_deactivate_max,
            description=ButtonPhrases.command_deactivate_max_desc,
        ),
    ]

    await bot.set_my_commands(
        commands=private_commands, scope=BotCommandScopeAllPrivateChats()
    )

    await bot.set_my_commands(
        commands=group_commands, scope=BotCommandScopeAllGroupChats()
    )
