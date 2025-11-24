import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import BigInteger, TIMESTAMP, func
from sqlalchemy.ext.asyncio import AsyncAttrs

# Simple Snowflake Generator (Conceptual)
# 실무에서는 별도의 Singleton ID Generator Class나 DB Sequence를 사용합니다.
def generate_snowflake_id() -> int:
    return int(time.time() * 1000) 

class Base(AsyncAttrs, DeclarativeBase):
    pass

class BaseEntityMixin:
    """모든 엔티티가 상속받는 공통 필드 (Audit & ID)"""
    
    id: Mapped[int] = mapped_column(
        BigInteger, 
        primary_key=True, 
        default=generate_snowflake_id,
        sort_order=-1  # ID가 항상 맨 앞에 오도록
    )
    
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=func.now(),
        nullable=False
    )

    # updated_at 등의 필드가 필요하다면 여기에 추가