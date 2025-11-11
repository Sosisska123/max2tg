from typing import Optional
from pydantic import BaseModel

from parser.models.chat import ChatModel


class MaxAccountModel(BaseModel):
    tg_user_id: int
    phone: str
    token: str
    proxy: Optional[str]
    chat_list: Optional[list[ChatModel]]
