from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
)


class DBDependency:
    def __init__(self, db_url: str) -> None:
        self._engine = create_async_engine(url=db_url)
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._engine.dispose()

    async def dispose(self) -> None:
        """Dispose of the engine and close all connections."""
        await self._engine.dispose()

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def db_session(self) -> async_sessionmaker[AsyncSession]:
        return self._session_factory
