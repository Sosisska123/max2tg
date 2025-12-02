class Phrases:
    @staticmethod
    def first_greeting() -> str:
        return """здарова\n\nнужно зарегистрироваться, <b>/reg нпк</b>"""

    @staticmethod
    def start() -> str:
        return "че"

    @staticmethod
    def success() -> str:
        return "✅ Регистрация пройдена"

    @staticmethod
    def already_registered() -> str:
        return "уже зареган"

    # region MAX

    @staticmethod
    def max_forwarded_message_template(
        chat_name: str,
        sender_name: str,
        text: str,
        replied_msg_sender_name: str = None,
        replied_msg_text: str = None,
    ) -> str | tuple[str, str]:
        if replied_msg_sender_name and replied_msg_text:
            return (
                f"↪️ Forwarded {replied_msg_sender_name}: {replied_msg_text}",
                f"☁️ {chat_name} | {sender_name}: {text}",
            )
        else:
            return f"☁️ {chat_name} | {sender_name}: {text}"

    @staticmethod
    def max_chat_connection_success(chat_name: str) -> str:
        return f"✅ MAX чат <b>{chat_name}</b> успешно подписан"

    @staticmethod
    def max_chat_disconnection_success(chat_name: str) -> str:
        return f"❌ MAX чат <b>{chat_name}</b> успешно отписан"

    @staticmethod
    def max_registration_required() -> str:
        return f"❌ Аккаунт <b>MAX</b> не привязан в боте. Чтобы получить список чатов и получать сообщения нужно войти /{ButtonPhrases.command_max_reg}"

    @staticmethod
    def max_login_success() -> str:
        return f"✅ <b>MAX</b> успешно привязан. Теперь перейдите в группу, <b>в которую</b> должны пересылаться сообщения из MAX и введите /{ButtonPhrases.command_subscribe_max}"

    @staticmethod
    def max_already_logged() -> str:
        return "⚠️ MAX уже зарегистрирован"

    @staticmethod
    def max_phone_number_request() -> str:
        return "Введите существующий номер, с которого нужно войти в MAX +71234567890"

    @staticmethod
    def max_wait_for_phone_acception(phone_number: str) -> str:
        return f"СМС отправлено на номер {phone_number}. ⌛ Подождите пока пройдет верификация"

    @staticmethod
    def max_request_sms() -> str:
        return "✅ <b>Теперь пришлите смс код</b>"

    @staticmethod
    def wait_for_confirmation() -> str:
        return "⌛ Ожидание подтверждения..."

    @staticmethod
    def max_same_user_error(created_user_id: int) -> str:
        return f"⚠️ Эта группа подписана <code>{created_user_id}</code>! только тот, кто подписал группу может ее отписать"

    @staticmethod
    def group_connected_success(group_name: str, creator_id: int, username: str) -> str:
        return f"✅ Группа <b>{group_name}</b> подписана\nID создателя: <code>{creator_id}</code> | Username: <code>{username}</code>\nТеперь выберите чат <b>MAX из</b> которого будут пересылаться сообщения:"

    @staticmethod
    def group_disconnected_success(group_name: str) -> str:
        return f"❌ Группа <b>{group_name}</b> успешно отписана"

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
    def user_not_found() -> str:
        return "⚠️ /start to регистрации"

    @staticmethod
    def flood_warning(time: int) -> str:
        return f"⚠️ Не так быстро! Подождите немного перед следующим действием. <code>{time}</code> сек"

    @staticmethod
    def wrong_chat_type() -> str:
        return "⚠️ Wrong chat type! Chat must be group or supergroup"

    @staticmethod
    def group_already_connected(group_name: str) -> str:
        return f"⚠️ Группа <b>{group_name}</b> уже подключена"

    @staticmethod
    def group_never_connected(group_name: str) -> str:
        return f"⚠️ Группа <b>{group_name}</b> не подключена"

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

    @staticmethod
    def max_reg_help() -> str:
        return (
            f"/{ButtonPhrases.command_max_reg} -- Добавить аккаунт в бота\n"
            f"/{ButtonPhrases.command_subscribe_max} -- Подписать группу, выбрать чат и получать сообщения в группе\n"
            f"/{ButtonPhrases.command_unsubscribe_max} —- Отписать эту группу (не пересылать сообщения)\n"
            f"/{ButtonPhrases.command_max_delete} —- Удалить регистрацию в боте (не работает)\n"
            f"/{ButtonPhrases.command_max_reconnect} —- Поменять читаемый чат в группе\n"
        )

    command_max_help = "max_help"
    command_max_reg = "max_reg"
    command_max_delete = "max_delete"
    command_max_reconnect = "max_recon"
    command_subscribe_max: str = "max_sub"
    command_unsubscribe_max: str = "max_unsub"
    command_subscribe_max_desc: str = (
        "Mark this group as connected to the MAX forwarding"
    )
    command_unsubscribe_max_desc: str = (
        "Unmark this group as connected to the MAX forwarding"
    )

    command_max_help_desc: str = "Помощь по подключению макса"
