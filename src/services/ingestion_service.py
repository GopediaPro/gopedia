"""
Document ingestion with concurrent chunk annotation.

Layers:
- Controller: validates DTO, calls IngestionService.ingest (not included here).
- Service: orchestrates fetch → macro summary/tags → chunk → micro summary/embedding → persist.
- Repository: DB adapters used by the service (pass in session-level methods).

Key feature: Step 5 (chunk annotation) is parallelized with asyncio.gather and
rate-limit aware semaphores to avoid serial LLM/embedding calls when a document
expands into many chunks.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable, List, Optional, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import ChunkNode, Revision


# -----------------------------------------------------------------------------
# Interfaces
# -----------------------------------------------------------------------------


class EmbeddingClient(Protocol):
    """Embedding client abstraction to keep vendors swappable."""

    async def embed_text(
        self,
        text: str,
        *,
        model: str,
        dimensions: Optional[int] = None,
        max_retries: int = 2,
    ) -> list[float]:
        ...


class Summarizer(Protocol):
    """LLM summarizer abstraction (macro or micro)."""

    async def summarize(
        self, text: str, *, context: Optional[str] = None, max_retries: int = 2
    ) -> str:
        ...


# -----------------------------------------------------------------------------
# DTOs
# -----------------------------------------------------------------------------


@dataclass
class ChunkInput:
    """Raw chunk produced by the chunker."""

    content: str
    chunk_type: str  # e.g., markdown_section, code_function
    ord: int
    meta: dict[str, Any]


@dataclass
class ChunkAnnotated:
    """Chunk with LLM summary and embedding ready for persistence."""

    content_summary: str
    embedding: list[float]
    chunk_type: str
    ord: int
    chunk_hash: str
    meta: dict[str, Any]


@dataclass
class ChunkingConfig:
    max_tokens: int = 800
    overlap_ratio: float = 0.12  # 12% overlap to preserve context
    language_hint: Optional[str] = None


@dataclass
class EmbeddingConfig:
    model: str = "text-embedding-3-small"
    max_retries: int = 2
    max_concurrency: int = 8  # tune per rate-limit window
    rate_limit_per_sec: Optional[int] = None  # e.g., 10 → 10 calls/sec
    target_dimension: int = 1536  # ensures gemini-embedding-001 uses 1536-d output


# -----------------------------------------------------------------------------
# Service
# -----------------------------------------------------------------------------


class IngestionService:
    """
    Orchestrates document ingestion. Controller should inject:
    - chunker: Callable[[str, ChunkingConfig], list[ChunkInput]]
    - macro_summarizer: Summarizer
    - micro_summarizer: Summarizer
    - embedding_client: EmbeddingClient
    - repo callbacks: create_revision, bulk_insert_chunks
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        chunker: Callable[[str, ChunkingConfig], list[ChunkInput]],
        macro_summarizer: Summarizer,
        micro_summarizer: Summarizer,
        embedding_client: EmbeddingClient,
    ) -> None:
        self.session = session
        self.chunker = chunker
        self.macro_summarizer = macro_summarizer
        self.micro_summarizer = micro_summarizer
        self.embedding_client = embedding_client

    async def ingest_document(
        self,
        *,
        raw_text: str,
        revision: Revision,
        chunk_cfg: ChunkingConfig,
        embed_cfg: EmbeddingConfig,
    ) -> list[ChunkNode]:
        """
        Execute steps 2-5 of the spec for a single document.
        - Step 2: macro summary/tags handled upstream; revision passed in.
        - Step 3: chunk split via injected chunker.
        - Step 4/5: per-chunk summary + embedding (concurrent).
        - Step 5: bulk persist chunk nodes.
        """
        chunks = self.chunker(raw_text, chunk_cfg)

        macro_summary = revision.meta_diff.get("macro_summary") if revision.meta_diff else None
        if not macro_summary:
            macro_summary = await self.macro_summarizer.summarize(
                raw_text, context=None, max_retries=embed_cfg.max_retries
            )

        annotated = await self._annotate_chunks_concurrently(
            chunks=chunks,
            macro_summary=macro_summary,
            embed_cfg=embed_cfg,
        )

        chunk_nodes = [
            ChunkNode(
                revision_id=revision.id,
                chunk_hash=item.chunk_hash,
                chunk_type=item.chunk_type,
                content_summary=item.content_summary,
                embedding=item.embedding,
                ord=item.ord,
            )
            for item in annotated
        ]

        self.session.add_all(chunk_nodes)
        return chunk_nodes

    async def _annotate_chunks_concurrently(
        self,
        *,
        chunks: Iterable[ChunkInput],
        macro_summary: str,
        embed_cfg: EmbeddingConfig,
    ) -> list[ChunkAnnotated]:
        """
        Step 5: parallel chunk summarization + embedding with rate-limit control.
        """
        semaphore = asyncio.Semaphore(embed_cfg.max_concurrency)
        tasks: list[Awaitable[ChunkAnnotated]] = []

        for chunk in chunks:
            tasks.append(
                self._annotate_single_chunk(
                    chunk=chunk,
                    macro_summary=macro_summary,
                    embed_cfg=embed_cfg,
                    semaphore=semaphore,
                )
            )

        results = await asyncio.gather(*tasks)
        # Keep original order stable
        return sorted(results, key=lambda c: c.ord)

    async def _annotate_single_chunk(
        self,
        *,
        chunk: ChunkInput,
        macro_summary: str,
        embed_cfg: EmbeddingConfig,
        semaphore: asyncio.Semaphore,
    ) -> ChunkAnnotated:
        """
        One chunk → micro summary + embedding with retries and optional rate-limit sleep.
        """
        async with semaphore:
            if embed_cfg.rate_limit_per_sec:
                await asyncio.sleep(1 / embed_cfg.rate_limit_per_sec)

            micro_summary = await self.micro_summarizer.summarize(
                chunk.content,
                context=macro_summary,
                max_retries=embed_cfg.max_retries,
            )

            text_for_embedding = f"{macro_summary}\n\n{micro_summary}\n\n{chunk.content}"
            embedding = await self.embedding_client.embed_text(
                text_for_embedding,
                model=embed_cfg.model,
                dimensions=embed_cfg.target_dimension,
                max_retries=embed_cfg.max_retries,
            )

            chunk_hash = _sha256_hex(chunk.content)

            if embed_cfg.target_dimension and len(embedding) != embed_cfg.target_dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {embed_cfg.target_dimension}, got {len(embedding)}"
                )

            return ChunkAnnotated(
                content_summary=micro_summary,
                embedding=embedding,
                chunk_type=chunk.chunk_type,
                ord=chunk.ord,
                chunk_hash=chunk_hash,
                meta=chunk.meta,
            )


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _sha256_hex(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()

