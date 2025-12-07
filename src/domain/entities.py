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
    """Base class for all SQLAlchemy models with async support."""
    pass


class BaseEntity(Base):
    """
    Base entity with common fields: ID and created_at timestamp.
    All entities that need these common fields should inherit from this class.
    """
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )
    modified_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=lambda: datetime.now(timezone.utc), 
        nullable=False
    )

# -----------------------------------------------------------------------------
# 1. System Dictionary (Normalization Engine)
# -----------------------------------------------------------------------------

class SysDict(BaseEntity):
    """
    System Dictionary for normalizing repeated strings (Tag, Type, Source).
    Stores categories like 'TAG', 'DTYPE', 'SOURCE', 'PRED' with their values.
    """
    __tablename__ = "sys_dict"
    
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    val: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("category", "val", name="uq_sys_dict_cat_val"),
    )


# -----------------------------------------------------------------------------
# 2. Blob Store (Content Addressable Storage)
# -----------------------------------------------------------------------------

class BlobStore(Base):
    """
    Content-addressable storage for text and binary data.
    Uses SHA-256 hash to eliminate duplication.
    """
    __tablename__ = "blob_store"

    hash: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(50), default="text/markdown")
    body: Mapped[bytes] = mapped_column(BYTEA, nullable=False)

# -----------------------------------------------------------------------------
# 3. Origin Data (Identity Layer - Immutable)
# -----------------------------------------------------------------------------

class OriginData(BaseEntity):
    """
    The identity layer - immutable identifier for data.
    URN remains constant even when location or content changes.
    Format: "urn:rhizome:<dtype>:<uuid>"
    """
    __tablename__ = "origin_data"

    urn: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    
    # Foreign Keys
    src_sys_id: Mapped[int] = mapped_column(ForeignKey("sys_dict.id"), nullable=False)
    dtype_id: Mapped[int] = mapped_column(ForeignKey("sys_dict.id"), nullable=False)
    
    # Metadata
    props: Mapped[Dict[str, Any]] = mapped_column(JSONB, default={}, nullable=False)
    flags: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Circular FK to current revision
    curr_rev_id: Mapped[Optional[int]] = mapped_column(ForeignKey("revisions.id"), nullable=True)

    # Relationships
    source_system: Mapped[SysDict] = relationship("SysDict", foreign_keys=[src_sys_id])
    data_type: Mapped[SysDict] = relationship("SysDict", foreign_keys=[dtype_id])
    
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
# 4. Revisions (Macro Context Layer)
# -----------------------------------------------------------------------------

class Revision(BaseEntity):
    """
    Document revision history with whole-document embeddings.
    Stores macro-level context for general topic searches (Forest View).
    """
    __tablename__ = "revisions"

    data_id: Mapped[int] = mapped_column(
        ForeignKey("origin_data.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    summary_hash: Mapped[Optional[str]] = mapped_column(
        ForeignKey("blob_store.hash"), 
        nullable=True
    )
    
    # Search Strategy 1: Macro Embedding (Forest View)
    tags: Mapped[Optional[List[int]]] = mapped_column(ARRAY(BigInteger), nullable=True)
    embedding: Mapped[Optional[Any]] = mapped_column(Vector(1536), nullable=True)
    
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
    
    chunks: Mapped[List["ChunkNode"]] = relationship(
        "ChunkNode",
        back_populates="revision",
        cascade="all, delete-orphan"
    )


# -----------------------------------------------------------------------------
# 5. Tree Nodes (Location Layer - Mutable)
# -----------------------------------------------------------------------------

class TreeNode(BaseEntity):
    """
    User-facing folder structure. Handles data location/organization.
    Names and positions are mutable, unlike OriginData URNs.
    """
    __tablename__ = "tree_nodes"

    # Structure
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("tree_nodes.id", ondelete="CASCADE"), 
        nullable=True
    )
    data_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("origin_data.id", ondelete="SET NULL"), 
        nullable=True
    )
    
    # Visual Context
    view_type: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Virtual Path Assembly - URL-safe slug for path generation
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    
    ord: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("parent_id", "slug", "view_type", name="uq_tree_node_slug"),
    )

    # Relationships
    parent: Mapped[Optional["TreeNode"]] = relationship(
        "TreeNode", 
        remote_side="TreeNode.id", 
        back_populates="children"
    )
    children: Mapped[List["TreeNode"]] = relationship(
        "TreeNode", 
        back_populates="parent"
    )
    data: Mapped[Optional[OriginData]] = relationship("OriginData")


# -----------------------------------------------------------------------------
# 6. Knowledge Edges (Explicit Graph Layer)
# -----------------------------------------------------------------------------

class KnowledgeEdge(Base):
    """
    Explicit, confirmed logical relationships between data.
    Stores facts, not AI inferences.
    """
    __tablename__ = "knowledge_edges"

    source_id: Mapped[int] = mapped_column(
        ForeignKey("origin_data.id", ondelete="CASCADE"), 
        nullable=False,
        primary_key=True
    )
    target_id: Mapped[int] = mapped_column(
        ForeignKey("origin_data.id", ondelete="CASCADE"), 
        nullable=False,
        primary_key=True
    )
    predicate_id: Mapped[int] = mapped_column(
        ForeignKey("sys_dict.id"), 
        nullable=False,
        primary_key=True
    )
    
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationships
    source: Mapped[OriginData] = relationship("OriginData", foreign_keys=[source_id])
    target: Mapped[OriginData] = relationship("OriginData", foreign_keys=[target_id])
    predicate: Mapped[SysDict] = relationship("SysDict", foreign_keys=[predicate_id])


# -----------------------------------------------------------------------------
# 7. Chunk Nodes (Micro Context Layer - MVP)
# -----------------------------------------------------------------------------

class ChunkNode(Base):
    """
    Document chunks for pinpoint search and partial updates.
    Stores micro-level embeddings for specific question answering (Tree View).
    """
    __tablename__ = "chunk_nodes"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    revision_id: Mapped[int] = mapped_column(
        ForeignKey("revisions.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    chunk_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False)
    chunk_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    content_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Search Strategy 2: Micro Embedding (Tree View)
    embedding: Mapped[Optional[Any]] = mapped_column(Vector(1536), nullable=True)
    
    ord: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    revision: Mapped[Revision] = relationship("Revision", back_populates="chunks")
