from models.user import Base
import datetime
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column


# saved schedule before accepting
class TempSchedule(Base):
    __tablename__ = "temp_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    group: Mapped[str] = mapped_column(String(10))
    file_type: Mapped[str] = mapped_column(String(10))
    files_url: Mapped[str] = mapped_column(Text, unique=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        default=datetime.datetime.now()
    )
