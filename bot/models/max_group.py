from typing import Optional

from models.user import Base

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Group(Base):
    __tablename__ = "groups"

    # sqlalc id
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # group name
    group_title: Mapped[str] = mapped_column(String(100))
    # telegram or max id, ex: -10000000
    self_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    # telegram id of the user who created this group
    creator_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    # MAX chat ID thet this group references to
    connected_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    # max chat setting ext
    max_config: Mapped[Optional["MaxGroupConfig"]] = relationship(
        "MaxGroupConfig", back_populates="group", uselist=False
    )


# cached user saved groups
class MaxGroupConfig(Base):
    __tablename__ = "max_group_configs"

    # sqlalc id
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # telegram id
    owner_id: Mapped[int] = mapped_column(BigInteger)
    # max chat id
    chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=True)
    # max chat title
    chat_title: Mapped[str] = mapped_column(String(100), nullable=True)
    # last message in max chat
    last_message_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    # messages count in max chat
    messages_count: Mapped[int] = mapped_column(BigInteger, nullable=True)

    group: Mapped[Optional["Group"]] = relationship(
        "Group", back_populates="max_config"
    )

    connected_group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.self_id"), unique=True, nullable=True
    )
