from sqlalchemy import BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger, unique=True)

    username: Mapped[str] = mapped_column(unique=True)
    notification_state: Mapped[bool] = mapped_column(default=True)
    group: Mapped[int] = mapped_column(nullable=True)


# class Homework(Base):
#     __tablename__ = "homeworks"

#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
#     lesson_name: Mapped[str]
#     sharaga: Mapped[str] = mapped_column(String(10))
#     is_pinned: Mapped[bool] = mapped_column(default=False)
#     homework: Mapped[str] = mapped_column(String(1000))
#     useful_links: Mapped[Optional[str]] = mapped_column(String(500))

#     __table_args__ = (
#         UniqueConstraint("lesson_name", "sharaga", "homework", name="uq_lesson_sh_hw"),
#     )
