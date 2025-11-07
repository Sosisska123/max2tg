import datetime
from typing import Optional

from models.user import Base

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column


# Either can be a MAX Listening group and a Telegram Subscribed group
class GGroup(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # sql id
    group_link: Mapped[str] = mapped_column(unique=True)  # telegram id, ex: -10000000
    title: Mapped[str] = mapped_column(String(100))  # group name
    is_max: Mapped[bool] = mapped_column(
        default=False
    )  # as i mentioned above, this object can be either a max chat and a telegram group
    connected_group: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True
    )  # if this is a MAX chat it should have a link to the connected Telegram group
    created_user_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True
    )  # telegram id of an user who created this group

    created_at: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now()
    )


# Single stored message, with media if it has
class FMessages(Base):
    __tablename__ = "forwarded_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # sql id
    message_text: Mapped[str] = mapped_column(String(1000))  # message text
    media_link: Mapped[str] = mapped_column(String(3000))  # media link
    message_id: Mapped[int] = mapped_column(nullable=True)  # its own message ID
    reply_to_message_id: Mapped[int] = mapped_column(nullable=True)  # reply to message

    created_at: Mapped[datetime.datetime] = mapped_column(
        default=lambda: datetime.datetime.now()
    )
