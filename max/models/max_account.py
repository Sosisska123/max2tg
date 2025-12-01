from sqlalchemy import BigInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class MaxBase(DeclarativeBase):
    pass


class MaxAccount(MaxBase):
    __tablename__ = "max_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)

    # MAX account owner Telegram ID
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    # User Token to login
    token: Mapped[str] = mapped_column(String(1000))
