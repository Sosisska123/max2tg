from typing import Optional
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MaxAccount(Base):
    __tablename__ = "max_saved_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)

    # MAX account owner Telegram ID
    user_tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    # User Token to login
    token: Mapped[str] = mapped_column(String(1000))
    # Target litening MAX chat
    target_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
