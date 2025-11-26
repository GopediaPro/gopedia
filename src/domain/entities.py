from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict
from uuid import uuid4
import enum

from sqlalchemy import (
    BigInteger, String, Text, Boolean, DateTime, ForeignKey, 
    Integer, Float, CHAR, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB, BYTEA, ARRAY
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, 
    validates
)
from sqlalchemy.ext.asyncio import AsyncAttrs
from pgvector.sqlalchemy import Vector  # Requires pgvector installed

# -----------------------------------------------------------------------------
# Base & Mixins
# -----------------------------------------------------------------------------

class Base(AsyncAttrs, DeclarativeBase):
    pass

class BaseEntityMixin:
    """
    Common fields for all entities: ID, Created/Updated timestamps.
    Note: The user specified 'Created/Updated users' in the prompt, 
    but since Auth is just another data type in this system, 
    we might link to sys_dict or origin_data for users. 
    For now, we'll keep it simple with timestamps.
    """
    # Using BigInteger for IDs as per schema (Snowflake ID preferred in production)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    # updated_at is not in the provided SQL schema for all tables, 
    # but is good practice. We will add it where appropriate or strictly follow SQL.
    # The SQL schema provided 'created_at' for most tables.

# -----------------------------------------------------------------------------
# 1. System Dictionary
# -----------------------------------------------------------------------------

class SysDict(BaseEntityMixin, Base):
    __tablename__ = "sys_dict"
    
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    val: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("category", "val", name="uq_sys_dict_cat_val"),
    )

# -----------------------------------------------------------------------------
# 2. Blob Store
# -----------------------------------------------------------------------------

class BlobStore(Base):
    __tablename__ = "blob_store"

    hash: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(50), default="text/markdown")
    body: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

# -----------------------------------------------------------------------------
# 3. Origin Data (The Rhizome Core)
# -----------------------------------------------------------------------------

class OriginData(BaseEntityMixin, Base):
    __tablename__ = "origin_data"

    urn: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    # Foreign Keys
    src_sys_id: Mapped[int] = mapped_column(ForeignKey("sys_dict.id"), nullable=False)
    dtype_id: Mapped[int] = mapped_column(ForeignKey("sys_dict.id"), nullable=False)
    
    # Metadata
    props: Mapped[Dict[str, Any]] = mapped_column(JSONB, default={}, nullable=False)
    flags: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    curr_rev_id: Mapped[Optional[int]] = mapped_column(ForeignKey("revisions.id"), nullable=True)

    # Relationships
    source_system: Mapped[SysDict] = relationship("SysDict", foreign_keys=[src_sys_id])
    data_type: Mapped[SysDict] = relationship("SysDict", foreign_keys=[dtype_id])
    
    # Current revision relationship (Circular)
    # We use a string for the class name to avoid circular import issues if split files,
    # but here they are in the same file.
    current_revision: Mapped[Optional["Revision"]] = relationship(
        "Revision", 
        foreign_keys=[curr_rev_id], 
        post_update=True
    )
    
    revisions: Mapped[List["Revision"]] = relationship(
        "Revision", 
        foreign_keys="Revision.data_id", 
        back_populates="origin_data",
        cascade="all, delete-orphan"
    )

# -----------------------------------------------------------------------------
# 4. Revisions
# -----------------------------------------------------------------------------

class Revision(BaseEntityMixin, Base):
    __tablename__ = "revisions"

    data_id: Mapped[int] = mapped_column(ForeignKey("origin_data.id", ondelete="CASCADE"), nullable=False)
    
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    summary_hash: Mapped[Optional[str]] = mapped_column(ForeignKey("blob_store.hash"), nullable=True)
    
    # Context Injection
    tags: Mapped[Optional[List[int]]] = mapped_column(ARRAY(BigInteger), nullable=True)
    # embedding: Mapped[Optional[Any]] = mapped_column(Vector(1536), nullable=True) 
    # Note: Vector type requires pgvector installed in DB. 
    # For now, we define it but it might need 'mapped_column(Vector(1536))'
    
    editor_id: Mapped[int] = mapped_column(ForeignKey("sys_dict.id"), nullable=False)
    meta_diff: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Relationships
    origin_data: Mapped[OriginData] = relationship(
        "OriginData", 
        foreign_keys=[data_id], 
        back_populates="revisions"
    )
    summary_blob: Mapped[Optional[BlobStore]] = relationship("BlobStore")
    editor: Mapped[SysDict] = relationship("SysDict", foreign_keys=[editor_id])

# -----------------------------------------------------------------------------
# 5. Knowledge Edges (Graph)
# -----------------------------------------------------------------------------

class KnowledgeEdge(Base):
    __tablename__ = "knowledge_edges"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True) # Identity in SQL

    source_id: Mapped[int] = mapped_column(ForeignKey("origin_data.id", ondelete="CASCADE"), nullable=False)
    target_id: Mapped[int] = mapped_column(ForeignKey("origin_data.id", ondelete="CASCADE"), nullable=False)
    predicate_id: Mapped[int] = mapped_column(ForeignKey("sys_dict.id"), nullable=False)
    
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint("source_id", "target_id", "predicate_id", name="uq_edge_src_tgt_pred"),
    )

    # Relationships
    source: Mapped[OriginData] = relationship("OriginData", foreign_keys=[source_id])
    target: Mapped[OriginData] = relationship("OriginData", foreign_keys=[target_id])
    predicate: Mapped[SysDict] = relationship("SysDict", foreign_keys=[predicate_id])

# -----------------------------------------------------------------------------
# 6. Tree Nodes (Visualization Projection)
# -----------------------------------------------------------------------------

class TreeNode(BaseEntityMixin, Base):
    __tablename__ = "tree_nodes"

    # Structure
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tree_nodes.id", ondelete="CASCADE"), nullable=True)
    data_id: Mapped[Optional[int]] = mapped_column(ForeignKey("origin_data.id", ondelete="SET NULL"), nullable=True)
    
    # Visual Context
    view_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Rendering Config
    view_config: Mapped[Dict[str, Any]] = mapped_column(JSONB, default={}, nullable=True)
    ord: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("parent_id", "name", "view_type", name="uq_tree_node_sibling"),
    )

    # Relationships
    parent: Mapped[Optional["TreeNode"]] = relationship("TreeNode", remote_side="TreeNode.id", back_populates="children")
    children: Mapped[List["TreeNode"]] = relationship("TreeNode", back_populates="parent")
    data: Mapped[Optional[OriginData]] = relationship("OriginData")
