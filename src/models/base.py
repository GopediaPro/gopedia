import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy.sql import func

class Base(DeclarativeBase):
    """
    모든 SQLAlchemy 모델의 기본 클래스.
    공통 필드 (id, timestamps)를 정의합니다.
    """
    pass

class BaseModel(Base):
    """
    공통 필드를 포함하는 추상 기본 모델.
    실제 테이블로 매핑되지 않습니다.
    """
    __abstract__ = True

    # id는 UUID를 기본 키로 사용
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # 타임스탬프
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 사용자 정보 (MVP에서는 사용하지 않으나 확장성 고려)
    # created_by: Mapped[str | None] = mapped_column(String(255))
    # updated_by: Mapped[str | None] = mapped_column(String(255))

    # 테이블 이름을 클래스 이름(소문자)으로 자동 설정
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s" # 예: Anchor -> anchors