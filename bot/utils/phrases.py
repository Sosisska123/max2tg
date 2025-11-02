class Phrases:
    @staticmethod
    def first_greeting() -> str:
        return """здарова\n\nнужно зарегистрироваться, <b>/reg нпк</b>"""

    @staticmethod
    def start() -> str:
        return "че"

    @staticmethod
    def success() -> str:
        return "✅ Register success"

    @staticmethod
    def already_registered() -> str:
        return "уже зареган"

    @staticmethod
    def rings_knn() -> str:
        return "Exception: Index Out of Range Exception"

    @staticmethod
    def schedule_text(date: str) -> str:
        return f"расписание на {date}"

    @staticmethod
    def rings_npk(date: str) -> str:
        return f"🔔 расписание звонков {date}"

    @staticmethod
    def registration_required() -> str:
        return "⚠️ не рег. /reg <b>нпк</b> чтобы рег"

    @staticmethod
    def max_forwarded_message_template(
        max_chat: str, username: str, text: str, reply_message_id: int = None
    ) -> str:
        return (
            f"<b>{max_chat} | {username}</b>: {text}"
            if reply_message_id is None
            else f"<b>{username}</b>: {text}\n<i>Reply to {reply_message_id}</i>"
        )


class AdminPhrases:
    @staticmethod
    def admin_panel(users_count: int) -> str:
        return "[-] -- Admin Panel -- [-]"

    @staticmethod
    def admin_panel_stats(
        users_count: int, last_check_time_npk: str, last_check_time_knn: str
    ) -> str:
        return f"[-] -- Admin Panel -- [-]\n\n[сайт](https://pythonanywhere.com)\n\nЛошков - {users_count}\n\n**Последняя проверка NPK** - {last_check_time_npk}\n\n**Последняя проверка KNN** - {last_check_time_knn}"

    @staticmethod
    def load_schedule_text():
        return "send photo/document then"

    @staticmethod
    def comands_list():
        return (
            f"/{AdminPhrases.command_add_schedule} [нпк/кнн] [file/url] - загрузить расписание\n"
            f"/{AdminPhrases.command_add_ring_schedule} [нпк/кнн] [file/url] [reg/def] - добавить расписание звонков. reg - только на завтра, def - дефолтное\n"
            f"/{AdminPhrases.command_list_var} - список переменных бота\n"
            f"/{AdminPhrases.command_set_var} [var] [value] - изменить переменную бота\n"
            f"/{AdminPhrases.command_clear_jobs} - очистить планировщик проверки расписания ВК\n"
            f"/{AdminPhrases.command_list} - список команд\n"
            f"/{AdminPhrases.command_add_user} [id] [group] [username] - добавить пользователя\n"
            f"/{AdminPhrases.command_prikol} - все следующие расписания будут отправляться за 10 звезд. отключается после повторной отправки\n"
            f"/{AdminPhrases.command_mail_everyone} [message] [group] [ignore notification] - рассылка всем пользователям в группе. ignore notification - игнорировать отключенные уведомления у чела\n"
            f"/{AdminPhrases.command_list_subscribed_groups_max} - список всех подключенных групп\n"
            f"/{AdminPhrases.command_adm_activate_max} [group_id] - подписать группу на рассылку\n"
            f"/{AdminPhrases.command_adm_deactivate_max} [group_id] - отписать группу от рассылки\n"
            f"/{AdminPhrases.command_add_listening_chat_max} [max_chat_id] - добавить чат для прослушивания\n"
            f"/{AdminPhrases.command_remove_listening_chat_max} [max_chat_id] - удалить чат для прослушивания\n"
        )

    # region Admin Commands, Buttons

    check_npk_command: str = "Проверить NPK"
    check_knn_command: str = "Проверить KNN"
    load_schedule_command: str = "Загрузить расписание"

    # - - -

    approve_schdule_command: str = "✅ Подтвердить"
    approve_schdule_no_sound_command: str = "✅🔕 Подтвердить без звука"
    reject_schdule_command: str = "❌ Отклонить"
    edit_schdule_command: str = "✏️ Редактировать"

    # - - -

    command_add_schedule: str = "add_schedule"
    command_add_ring_schedule: str = "add_ring_schedule"
    command_list_var: str = "list_var"
    command_set_var: str = "set_var"
    command_clear_jobs: str = "clear_jobs"
    command_list: str = "list"
    command_add_user: str = "add_user"
    command_prikol: str = "prikol"
    command_mail_everyone: str = "mail"

    command_list_subscribed_groups_max: str = "max_subscribed_groups"
    command_adm_activate_max: str = "adm_subscribe"
    command_adm_deactivate_max: str = "adm_unsubscribe"

    command_add_listening_chat_max: str = "add_listening_chat"
    command_remove_listening_chat_max: str = "remove_listening_chat"

    # endregion


# ERROR MESSAGES


class ErrorPhrases:
    @staticmethod
    def invalid() -> str:
        return "⚠️ invalid"

    @staticmethod
    def something_went_wrong() -> str:
        return "⚠️ что-то пошло не так"

    @staticmethod
    def group_not_found() -> str:
        return "⚠️ нет такой группы"

    @staticmethod
    def length_error() -> str:
        return "⚠️ слишком длинный"

    @staticmethod
    def ai_request_failed() -> str:
        return "⚠️ произошла ошибка при обработке запроса"

    @staticmethod
    def value_error() -> str:
        return "⚠️ ValueError"

    @staticmethod
    def user_not_found() -> str:
        return "⚠️ /start to регистрации"

    @staticmethod
    def flood_warning(time: int) -> str:
        return f"⚠️ Не так быстро! Подождите немного перед следующим действием. <code>{time}</code> сек"

    @staticmethod
    def wrong_file_type() -> str:
        return "wrong file type"

    @staticmethod
    def wrong_chat_type() -> str:
        return "⚠️ Wrong chat type! Chat must be group or supergroup"

    @staticmethod
    def chat_already_connected(chat_name: str) -> str:
        return f"⚠️ {chat_name.capitalize()} already connected"

    @staticmethod
    def chat_never_connected(chat_name: str) -> str:
        return f"⚠️ {chat_name.capitalize()} never connected"


class ButtonPhrases:
    lessons_command: str = "lessons"
    today_command: str = "today"
    homework_command: str = "homework"
    rings_command: str = "rings"

    # ---

    lessons_command_desc: str = "расписание на завтра"
    today_command_desc: str = "расписание на сегодня"
    homework_command_desc: str = "дз срочно"
    rings_command_desc: str = "звонки"

    # ---

    lessons_command_panel: str = "🧾 Расписание tomorrow"
    today_command_panel: str = "📝 Расписание на сегодня"
    rings_command_panel: str = "🛎️ Расписание звонков"
    settings_command_panel: str = "⚙️ Настройки"

    # ---

    turn_off_notifications_command: str = "🔕 Отключить уведомления"
    turn_on_notifications_command: str = "✅ Включить уведомления"

    # - - -

    command_activate_max: str = "max_subscribe"
    command_activate_max_desc: str = (
        "Mark this group as connected to the MAX forwarding"
    )
    command_deactivate_max: str = "max_unsubscribe"
    command_deactivate_max_desc: str = (
        "Unmark this group as connected to the MAX forwarding"
    )
