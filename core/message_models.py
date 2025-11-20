from typing import Literal, Optional
from pydantic import BaseModel


class MessageModel(BaseModel):
    type: str
    user_id: int


class Attach(BaseModel):
    base_url: str

    # idk
    photo_id: Optional[str] = None


class PhoneConfirmedMessage(MessageModel):
    type: Literal["phone_confirmed"] = "phone_confirmed"
    token: str


class SMSConfirmedMessage(MessageModel):
    type: Literal["sms_confirmed"] = "sms_confirmed"


class FetchChatsMessage(MessageModel):
    type: Literal["fetch_chats"] = "fetch_chats"
    chat_id: int
    chat_title: str
    messages_count: int
    last_message_id: int


class SendChatListMessage(MessageModel):
    type: Literal["send_chat_list"] = "send_chat_list"
    all_message: dict


class StartAuthMessage(MessageModel):
    type: Literal["start_auth"] = "start_auth"
    phone: str


class VerifyCodeMessage(MessageModel):
    type: Literal["verify_code"] = "verify_code"
    token: str
    code: str


class SubscribeToChatMessage(MessageModel):
    type: Literal["subscribe_to_chat"] = "subscribe_to_chat"
    chat_id: str


class ChatMsgMessage(MessageModel):
    """Base message model for any chat messages"""

    type: Literal["new_chat_message"] = "new_chat_message"
    sender_id: str
    message_id: str
    timestamp: int
    text: str
    attachments: Optional[list[Attach]] = None
    replied_msg: Optional["ChatMsgMessage"] = None
