import enum
import uuid
from sqlalchemy import Column, String, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, Dict, Any

from src.models.base import BaseModel # BaseModel 임포트

class AnchorType(enum.Enum):
    """Anchor의 소스 유형"""
    GITHUB = "github"
    FILESYSTEM = "filesystem"
    TODO = "todo"
    CALENDAR = "calendar"
    # ... 추가 가능

class Anchor(BaseModel):
    """
    연결 대상 (Source) 모델.
    GitHub 파일, Todo 항목 등 외부 리소스를 가리킵니다.
    """
    __tablename__ = "anchors"

    type: Mapped[AnchorType] = mapped_column(Enum(AnchorType), nullable=False, index=True)
    
    # 예: "github:org/repo/path/to/file.md"
    locator: Mapped[str] = mapped_column(String(1024), unique=True, index=True, nullable=False)
    
    # GitHub SHA, Node ID 등
    origin_id: Mapped[Optional[str]] = mapped_column(String(255))
    
    # metadata는 SQLAlchemy 예약어이므로 meta_data로 변경
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, name="metadata")

    # VirtualPage와의 1:1 관계 (Anchor -> VirtualPage)
    # todo [feat] VirtualPage 대표 페이지 선택기능(중복 가능)
    virtual_page: Mapped["VirtualPage"] = relationship(
        "VirtualPage", 
        back_populates="anchor", 
        cascade="all, delete-orphan"
    )

class VirtualPage(BaseModel):
    """
    가상 페이지 모델.
    하나의 Anchor에 1:1로 매핑되며, 요약 정보와 Outline ID를 가집니다.
    """
    __tablename__ = "virtual_pages"
    # todo [feat] VirtualPage 대표 페이지 선택기능(중복 가능)
    # Anchor와의 1:1 관계 (VirtualPage -> Anchor)
    anchor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("anchors.id"), unique=True, nullable=False
    )
    
    title: Mapped[Optional[str]] = mapped_column(String(512))
    
    # 내용 요약 (LLM 등으로 생성될 수 있음)
    content_summary: Mapped[Optional[str]] = mapped_column(Text)
    
    # 내용 설명 (GitHub 파일의 경우 Readme 내용 등)
    content_description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Outline 서비스에 발행된 문서의 ID
    outline_document_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)

    # Anchor 관계 정의
    anchor: Mapped[Anchor] = relationship(
        "Anchor", 
        back_populates="virtual_page",
        lazy="joined" # 페이지 조회 시 Anchor 정보도 함께 로드
    )

    # Revision과의 1:N 관계
    revisions: Mapped[List["Revision"]] = relationship(
        "Revision", 
        back_populates="virtual_page",
        cascade="all, delete-orphan"
    )

class Revision(BaseModel):
    """
    가상 페이지의 리비전 (MVP에서는 사용 X)
    """
    __tablename__ = "revisions"

    virtual_page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("virtual_pages.id"), nullable=False
    )
    
    # 리비전 내용 (예: 스냅샷)
    content_snapshot: Mapped[Optional[str]] = mapped_column(Text)
    
    revision_notes: Mapped[Optional[str]] = mapped_column(String(1024))

    # VirtualPage 관계 정의
    virtual_page: Mapped[VirtualPage] = relationship(
        "VirtualPage", 
        back_populates="revisions"
    )