from sqlalchemy import BigInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger, unique=True)

    username: Mapped[str] = mapped_column(String(30), unique=True)
    notification_state: Mapped[bool] = mapped_column(default=True)
    can_connect_max: Mapped[bool] = mapped_column(default=False)
