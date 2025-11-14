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

# 백그라운드 태스크용 세션 생성 함수
async def get_db_session() -> AsyncSession:
    """
    백그라운드 태스크 등에서 사용할 별도의 세션을 생성합니다.
    사용 후 반드시 세션을 닫아야 합니다.
    """
    return AsyncSessionLocal()

# 데이터베이스 연결 테스트 함수
async def test_database_connection() -> dict:
    """
    데이터베이스 연결을 테스트합니다.
    """
    try:
        async with AsyncSessionLocal() as session:
            # 간단한 쿼리로 연결 테스트
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            result.scalar()
            return {
                "status": "success",
                "message": "Database connection successful"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }

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
        # async with 구문이 자동으로 세션을 닫아주므로 finally에서 close() 호출 불필요