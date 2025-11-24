import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# [Gopedia Config Import]
# 1. 환경 변수 로드
from app.config import settings
# 2. 모델 메타데이터 로드 (여기에 정의된 테이블만 감지됨)
from domain.entities.base import Base
# 모든 모델 파일을 임포트해야 Base.metadata에 등록됩니다.
from domain.entities import models  # noqa

# Alembic Config 객체
config = context.config

# .env의 DATABASE_URL로 sqlalchemy.url 덮어쓰기
config.set_main_option("sqlalchemy.url", str(settings.DATABASE_URL))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 자동 생성을 위한 메타데이터 타겟 설정
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """오프라인 모드: DB 연결 없이 SQL 스크립트만 생성할 때 사용"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    """실제 마이그레이션 실행 로직"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """온라인 모드: 실제 DB에 연결하여 스키마 변경"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())