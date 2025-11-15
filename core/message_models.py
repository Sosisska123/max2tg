from pydantic import BaseModel


class MessageModel(BaseModel):
    type: str
    user_id: int


class PhoneConfirmedMessage(MessageModel):
    type: str = "phone_confirmed"
    token: str


class SMSConfirmedMessage(MessageModel):
    type: str = "sms_confirmed"


class FetchChatsMessage(MessageModel):
    type: str = "fetch_chats"
    all_message: dict


class SendChatListMessage(MessageModel):
    type: str = "send_chat_list"
    all_message: dict


class StartAuthMessage(MessageModel):
    type: str = "start_auth"
    phone: str


class VerifyCodeMessage(MessageModel):
    type: str = "verify_code"
    token: str
    code: str


class SubscribeToChatMessage(MessageModel):
    type: str = "subscribe_to_chat"
    chat_id: str
