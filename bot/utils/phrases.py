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

    # region MAX

    @staticmethod
    def max_forwarded_message_template(
        max_chat: str, username: str, text: str, reply_message_id: int = None
    ) -> str:
        return (
            f"<b>{max_chat} | {username}</b>: {text}"
            if reply_message_id is None
            else f"<b>{username}</b>: {text}\n<i>Reply to {reply_message_id}</i>"
        )

    @staticmethod
    def group_connected_success(group_name: str, creator_id: int) -> str:
        return f"✅ Group <b>{group_name}</b> has successfully connected. Creator ID: <code>{creator_id}</code>\nNow select the <b>MAX</b> chat to listen to:"

    @staticmethod
    def group_disconnected_success(group_name: str) -> str:
        return f"❌ Group <b>{group_name}</b> has successfully disconnected"

    @staticmethod
    def select_max_chat() -> str:
        return "Select the <i>MAX</i> chat to listen to:"

    @staticmethod
    def max_chat_connected_success(chat_name: str) -> str:
        return f"✅ MAX chat <b>{chat_name}</b> has successfully connected"

    @staticmethod
    def max_chat_disconnected_success(chat_name: str) -> str:
        return f"❌ MAX chat <b>{chat_name}</b> has successfully disconnected."

    @staticmethod
    def max_chat_already_connected(chat_name: str) -> str:
        return f"⚠️ MAX chat <b>{chat_name}</b> already connected."

    @staticmethod
    def max_chat_never_connected(chat_name: str) -> str:
        return f"⚠️ MAX chat <b>{chat_name}</b> never connected."

    @staticmethod
    def max_chat_list(chats: list) -> str:
        if not chats:
            return "No MAX chats connected."
        return "Connected MAX chats:\n" + "\n".join(
            [f"- <b>{chat}</b>" for chat in chats]
        )

    @staticmethod
    def max_chat_not_found() -> str:
        return "⚠️ MAX chat not found."

    @staticmethod
    def max_registration_required() -> str:
        return f"❌ Your <b>MAX</b> account is not set. <b>MAX Websocket</b> requires a phone number to login.\n\nTo continue type /{ButtonPhrases.command_max_help}"

    @staticmethod
    def max_login_success() -> str:
        return f"✅ MAX login success. Now move to your group where you want to receive notifications and type /{ButtonPhrases.command_activate_max}"

    @staticmethod
    def max_login_failed() -> str:
        return "⚠️ MAX login failed"

    @staticmethod
    def max_already_logged() -> str:
        return "⚠️ MAX already logged in"

    @staticmethod
    def max_phone_number_request() -> str:
        return "Please send your phone number to login to MAX. +71234567890"

    @staticmethod
    def max_wait_for_phone_acception(phone_number: str) -> str:
        return (
            f"Your number is +7{phone_number}. ⌛ Please wait until number is verified"
        )

    @staticmethod
    def max_request_sms() -> str:
        return "✅ <b>Now please send the code you received</b>"

    @staticmethod
    def wait_for_confirmation() -> str:
        return "⌛ Waiting for confirmation..."

    @staticmethod
    def max_same_user_error(created_user_id: int) -> str:
        return f"⚠️ This group was subscribed by <code>{created_user_id}</code>! Only the same user can unsubscribe groups and chats"

    # endregion


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

    @staticmethod
    def network_issues() -> str:
        return "❌ something went wrong with server. Please try again later"


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

    @staticmethod
    def max_reg_help() -> str:
        return (
            "Чтобы связать чат в <b>MAX</b> и группу <b>Телеграм</b>, нужен любой <b>номер телефона</b> который зарегистрирован в MAX и <b>находится в этом чате</b>\n\n"
            f"Только <b>одному</b> человеку нужно зарегистрироваться в этом боте и отправить сообщение /{ButtonPhrases.command_activate_max} в группу, <b>где уже находится этот бот</b>\n\n"
            f"/{ButtonPhrases.command_deactivate_max} — Чтобы отписать эту группу\n"
            f"/{ButtonPhrases.command_max_delete} — Для удаления регистрации в боте"
        )

    command_max_help = "max_help"
    command_max_reg = "max_reg"
    command_max_delete = "max_delete"
