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
