from models.user import Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


# Either can be a MAX Listening group and a Telegram Subscribed group
class GGroup(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # sql id
    group_link: Mapped[str] = mapped_column(unique=True)  # telegram id, ex: -10000000
    title: Mapped[str] = mapped_column(String(100))  # group name
    is_max: Mapped[bool] = mapped_column(default=False)


# Single stored message, with media if it has
class FMessages(Base):
    __tablename__ = "forwarded_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # sql id
    message_text: Mapped[str] = mapped_column(String(1000))  # message text
    media_link: Mapped[str] = mapped_column(String(3000))  # media link
    message_id: Mapped[int] = mapped_column(nullable=True)  # its own message ID
    reply_to_message_id: Mapped[int] = mapped_column(nullable=True)  # reply to message
