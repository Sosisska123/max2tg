from aiogram.fsm.state import State, StatesGroup


class LoadScheduleFsm(StatesGroup):
    select_group = State()
    load_file = State()
    load_rings = State()
    approve_schedule = State()


class SubscribeMaxChat(StatesGroup):
    select_listening_chat = State()


class LoginWithMax(StatesGroup):
    phone_number = State()
    phone_code = State()
