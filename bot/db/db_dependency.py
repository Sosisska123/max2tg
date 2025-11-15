from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)

from config import Settings


class DBDependency:
    def __init__(self, config: Settings) -> None:
        self._engine = create_async_engine(url=config.bot.db_url)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def db_session(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory
