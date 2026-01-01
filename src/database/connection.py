"""
데이터베이스 연결 관리
"""
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from ..config.settings import get_settings
from ..models.base import Base

settings = get_settings()

# 비동기 엔진 생성
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool,
    future=True
)

# 세션 팩토리
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def init_db():
    """데이터베이스 초기화 (테이블 생성)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """데이터베이스 연결 종료"""
    await engine.dispose()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """세션 의존성 주입용"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """데이터베이스 매니저"""

    def __init__(self):
        self._engine = None
        self._session_factory = None

    async def connect(self, database_url: Optional[str] = None):
        """데이터베이스 연결"""
        url = database_url or settings.database_url

        self._engine = create_async_engine(
            url,
            echo=settings.debug,
            poolclass=NullPool,
            future=True
        )

        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def disconnect(self):
        """연결 해제"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    async def create_tables(self):
        """테이블 생성"""
        if self._engine:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

    def get_session(self) -> AsyncSession:
        """세션 가져오기"""
        if not self._session_factory:
            raise RuntimeError("Database not connected")
        return self._session_factory()

    @property
    def is_connected(self) -> bool:
        """연결 상태"""
        return self._engine is not None


# 전역 인스턴스
db_manager = DatabaseManager()
