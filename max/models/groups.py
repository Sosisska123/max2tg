from typing import Optional

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from max.models.max_account import MaxBase


class Group(MaxBase):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group_title: Mapped[str] = mapped_column(String(100))
    group_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    user_tg_id: Mapped[int] = mapped_column(BigInteger)
    connected_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)


# cached user saved chats
class Chat(MaxBase):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_tg_id: Mapped[int] = mapped_column(BigInteger)
    chat_title: Mapped[str] = mapped_column(String(100))
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    last_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    messages_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
