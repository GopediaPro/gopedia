from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator

from src.core.config import settings

# 비동기 엔진 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True, # 개발 중에는 True로 설정하여 SQL 쿼리 로깅
    future=True
)

# 비동기 세션 메이커
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# SQLAlchemy 모델용 Base 클래스 (src/models/base.py에서도 정의하지만, 
# 여기서는 임포트만 하거나, base.py에서 DeclarativeBase를 직접 임포트)
# 여기서는 src/models/base.py에서 Base를 정의하고 사용한다고 가정합니다.
# from src.models.base import Base (순환 참조 주의)

# FastAPI Depends를 위한 비동기 세션 제너레이터
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI 의존성 주입을 위한 비동기 데이터베이스 세션 제너레이터
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # 트랜잭션 관리는 리포지토리 또는 서비스 레이어에서
            # await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()