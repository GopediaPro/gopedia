from typing import List, Optional, Any
from sqlalchemy import String, ForeignKey, Integer, Float, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, BYTEA, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector

from domain.entities.base import Base, BaseEntityMixin

# 1. System Dictionary
class SysDict(Base, BaseEntityMixin):
    __tablename__ = "sys_dict"
    
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    val: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    __table_args__ = (UniqueConstraint('category', 'val', name='uq_sys_dict_cat_val'),)

# 2. Blob Store (CAS)
class BlobStore(Base):
    __tablename__ = "blob_store"
    
    hash: Mapped[str] = mapped_column(String(64), primary_key=True) # SHA-256
    content_type: Mapped[str] = mapped_column(String(50), default="text/markdown")
    body: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

# 3. Origin Data (The Rhizome Root)
class OriginData(Base, BaseEntityMixin):
    __tablename__ = "origin_data"

    urn: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    # Foreign Keys
    src_sys_id: Mapped[int] = mapped_column(ForeignKey("sys_dict.id"))
    dtype_id: Mapped[int] = mapped_column(ForeignKey("sys_dict.id"))
    
    # Metadata for Querying (Reporting, Scoring, etc.)
    props: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default='{}')
    
    # State
    flags: Mapped[int] = mapped_column(Integer, default=0)
    
    # Circular FK Pointer (Nullable initially)
    curr_rev_id: Mapped[Optional[int]] = mapped_column(ForeignKey("revisions.id", use_alter=True))

    # Relationships
    latest_revision: Mapped["Revision"] = relationship(
        "Revision", 
        primaryjoin="OriginData.curr_rev_id == Revision.id",
        post_update=True
    )
    revisions: Mapped[List["Revision"]] = relationship(
        "Revision", 
        primaryjoin="OriginData.id == Revision.data_id",
        back_populates="origin_data"
    )

# 4. Revisions (Context & History)
class Revision(Base, BaseEntityMixin):
    __tablename__ = "revisions"

    data_id: Mapped[int] = mapped_column(ForeignKey("origin_data.id", ondelete="CASCADE"))
    
    # Content Pointer
    title: Mapped[Optional[str]] = mapped_column(String(512))
    summary_hash: Mapped[Optional[str]] = mapped_column(ForeignKey("blob_store.hash"))
    
    # Context Injection
    tags: Mapped[Optional[List[int]]] = mapped_column(ARRAY(BigInteger)) # Array of sys_dict ids
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536))
    
    # Traceability
    editor_id: Mapped[int] = mapped_column(ForeignKey("sys_dict.id"))
    meta_diff: Mapped[Optional[dict]] = mapped_column(JSONB)
    
    # Relationship back to OriginData
    origin_data: Mapped["OriginData"] = relationship(
        "OriginData", 
        primaryjoin="Revision.data_id == OriginData.id",
        back_populates="revisions"
    )

# 5. Knowledge Edges (Graph)
class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, sort_order=-1)
    
    source_id: Mapped[int] = mapped_column(ForeignKey("origin_data.id", ondelete="CASCADE"))
    target_id: Mapped[int] = mapped_column(ForeignKey("origin_data.id", ondelete="CASCADE"))
    predicate_id: Mapped[int] = mapped_column(ForeignKey("sys_dict.id"))
    
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint('source_id', 'target_id', 'predicate_id'),)