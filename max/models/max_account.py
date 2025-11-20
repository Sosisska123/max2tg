from typing import Optional
from pydantic import BaseModel

from .chat import ChatModel


class MaxAccountModel(BaseModel):
    tg_user_id: int
    phone: str
    token: str
    proxy: Optional[str] = None
    chat_list: Optional[list[ChatModel]] = None
