import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# --- .env 로드 및 src 경로 추가 ---
import os
import sys
from dotenv import load_dotenv

# 프로젝트 루트(alembic.ini가 있는 곳)의 .env 파일 로드
# alembic.ini가 프로젝트 루트에 있다고 가정
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# src 디렉터리를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
# --- 

# SQLAlchemy 모델 임포트 (Base.metadata를 위함)
from models.base import Base as BaseModel # src/models/base.py의 Base
from models import models # src/models/models.py (테이블 모델들 임포트)

# Alembic Config 객체 (context에서 사용)
config = context.config

# --- DATABASE_URL 설정 ---
# .env에서 로드한 값을 alembic.ini의 sqlalchemy.url 기본값으로 사용
# alembic.ini에서 ${DATABASE_URL}을 사용하기 때문에 이 부분이 필수
db_url = os.getenv("DATABASE_URL")
if not db_url:
    raise ValueError("DATABASE_URL 환경 변수가 설정되지 않았습니다.")
config.set_main_option("sqlalchemy.url", db_url)
# ---

# Logging 설정
if config.config_file_name:
    fileConfig(config.config_file_name)

# target_metadata
# autogenerate 지원을 위해 SQLAlchemy 모델의 metadata를 참조
target_metadata = BaseModel.metadata

# ... (기타 Alembic 설정) ...

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    ...
    """
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
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # config 객체에서 'sqlalchemy.' 접두사가 붙은 설정을 가져와
    # async 엔진을 설정합니다.
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