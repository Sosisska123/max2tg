from typing import Literal, Optional
from pydantic import BaseModel


class MessageModel(BaseModel):
    type: str
    user_id: int


class Attach(BaseModel):
    base_url: str
    type: Literal["photo"]

    # idk
    photo_id: Optional[str] = None


class PhoneSentMessage(MessageModel):
    type: Literal["phone_sent"] = "phone_sent"
    short_token: str


class SMSConfirmedMessage(MessageModel):
    type: Literal["sms_confirmed"] = "sms_confirmed"
    full_token: str


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
    # from bot
    type: Literal["start_auth"] = "start_auth"
    phone: str


class VerifyCodeMessage(MessageModel):
    # from bot
    type: Literal["verify_code"] = "verify_code"
    token: str
    code: str


class SubscribeToChatMessage(MessageModel):
    # from bot
    type: Literal["subscribe_to_chat"] = "subscribe_to_chat"
    chat_id: str


class ChatMsgMessage(MessageModel):
    """Base message model for any chat messages"""

    type: Literal["new_chat_message"] = "new_chat_message"
    sender_id: int
    chat_id: int
    message_id: str
    timestamp: int
    text: Optional[str] = None
    attaches: Optional[list[Attach]] = None
    replied_msg: Optional["ChatMsgMessage"] = None
