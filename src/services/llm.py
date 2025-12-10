from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable, Optional, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import ChunkNode, Revision

# -----------------------------------------------------------------------------
# Interfaces
# -----------------------------------------------------------------------------

class EmbeddingClient(Protocol):
    """Embedding client abstraction to keep vendors swappable."""
    async def embed_text(self, text: str, *, model: str, dimensions: Optional[int] = None, max_retries: int = 2) -> list[float]:
        ...

class Summarizer(Protocol):
    """LLM summarizer abstraction (macro or micro)."""
    async def summarize(self, text: str, *, context: Optional[str] = None, max_retries: int = 2) -> str:
        ...

# -----------------------------------------------------------------------------
# DTOs
# -----------------------------------------------------------------------------

@dataclass
class ChunkInput:
    """Raw chunk produced by the chunker."""
    content: str
    chunk_type: str
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
    overlap_ratio: float = 0.12
    language_hint: Optional[str] = None

@dataclass
class EmbeddingConfig:
    model: str = "text-embedding-3-small"
    max_retries: int = 2
    max_concurrency: int = 8
    rate_limit_per_sec: Optional[int] = None
    target_dimension: int = 1536

# -----------------------------------------------------------------------------
# Mock Implementations
# -----------------------------------------------------------------------------

class MockEmbeddingClient:
    async def embed_text(self, text: str, *, model: str, dimensions: Optional[int] = None, max_retries: int = 2) -> list[float]:
        return [0.0] * (dimensions or 1536)

class MockSummarizer:
    async def summarize(self, text: str, *, context: Optional[str] = None, max_retries: int = 2) -> str:
        return f"Summary of: {text[:100]}..."

def mock_chunker(text: str, config: ChunkingConfig) -> list[ChunkInput]:
    return [ChunkInput(content=text, chunk_type="mock", ord=0, meta={})]

# -----------------------------------------------------------------------------
# Service
# -----------------------------------------------------------------------------

class IngestionService:
    def __init__(self, session: AsyncSession, *, chunker: Callable[[str, ChunkingConfig], list[ChunkInput]], macro_summarizer: Summarizer, micro_summarizer: Summarizer, embedding_client: EmbeddingClient) -> None:
        self.session = session
        self.chunker = chunker
        self.macro_summarizer = macro_summarizer
        self.micro_summarizer = micro_summarizer
        self.embedding_client = embedding_client

    async def ingest_document(self, *, raw_text: str, revision: Revision, chunk_cfg: ChunkingConfig, embed_cfg: EmbeddingConfig) -> list[ChunkNode]:
        chunks = self.chunker(raw_text, chunk_cfg)
        macro_summary = revision.meta_diff.get("macro_summary") if revision.meta_diff else None
        if not macro_summary:
            macro_summary = await self.macro_summarizer.summarize(raw_text, context=None, max_retries=embed_cfg.max_retries)
        
        annotated = await self._annotate_chunks_concurrently(chunks=chunks, macro_summary=macro_summary, embed_cfg=embed_cfg)
        chunk_nodes = [ChunkNode(revision_id=revision.id, chunk_hash=item.chunk_hash, chunk_type=item.chunk_type, content_summary=item.content_summary, embedding=item.embedding, ord=item.ord) for item in annotated]
        
        self.session.add_all(chunk_nodes)
        return chunk_nodes

    async def _annotate_chunks_concurrently(self, *, chunks: Iterable[ChunkInput], macro_summary: str, embed_cfg: EmbeddingConfig) -> list[ChunkAnnotated]:
        semaphore = asyncio.Semaphore(embed_cfg.max_concurrency)
        tasks: list[Awaitable[ChunkAnnotated]] = [self._annotate_single_chunk(chunk=chunk, macro_summary=macro_summary, embed_cfg=embed_cfg, semaphore=semaphore) for chunk in chunks]
        results = await asyncio.gather(*tasks)
        return sorted(results, key=lambda c: c.ord)

    async def _annotate_single_chunk(self, *, chunk: ChunkInput, macro_summary: str, embed_cfg: EmbeddingConfig, semaphore: asyncio.Semaphore) -> ChunkAnnotated:
        async with semaphore:
            if embed_cfg.rate_limit_per_sec:
                await asyncio.sleep(1 / embed_cfg.rate_limit_per_sec)
            
            micro_summary = await self.micro_summarizer.summarize(chunk.content, context=macro_summary, max_retries=embed_cfg.max_retries)
            text_for_embedding = f"{macro_summary}\n\n{micro_summary}\n\n{chunk.content}"
            embedding = await self.embedding_client.embed_text(text_for_embedding, model=embed_cfg.model, dimensions=embed_cfg.target_dimension, max_retries=embed_cfg.max_retries)
            chunk_hash = _sha256_hex(chunk.content)

            if embed_cfg.target_dimension and len(embedding) != embed_cfg.target_dimension:
                raise ValueError(f"Embedding dimension mismatch: expected {embed_cfg.target_dimension}, got {len(embedding)}")

            return ChunkAnnotated(content_summary=micro_summary, embedding=embedding, chunk_type=chunk.chunk_type, ord=chunk.ord, chunk_hash=chunk_hash, meta=chunk.meta)

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _sha256_hex(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

from src.core.config import settings
from src.infrastructure.external.gemini_client import GeminiEmbeddingClient, GeminiSummarizer


# -----------------------------------------------------------------------------
# Real chunker implementation
# -----------------------------------------------------------------------------

def langchain_chunker(text: str, config: ChunkingConfig) -> list[ChunkInput]:
    """Chunk text using LangChain's text splitter."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.max_tokens,
        chunk_overlap=int(config.max_tokens * config.overlap_ratio),
        length_function=len,
    )
    chunks = splitter.split_text(text)
    return [
        ChunkInput(content=chunk, chunk_type="text", ord=i, meta={})
        for i, chunk in enumerate(chunks)
    ]

# -----------------------------------------------------------------------------
# Service Factory
# -----------------------------------------------------------------------------

def get_ingestion_service(session: AsyncSession) -> IngestionService:
    """
    Factory to get the right ingestion service based on provider settings.
    
    This function checks for an LLM_API_KEY in the settings. If present, it
    initializes and returns an IngestionService with real Gemini clients for
    embedding and summarization, along with a functional text chunker.
    
    If the API key is not found, it falls back to mock implementations for
    all components, ensuring that the application can run without a live
_llm_connection.
    """
    if settings.LLM_API_KEY:
        # Use real clients
        embedding_client = GeminiEmbeddingClient()
        macro_summarizer = GeminiSummarizer(generation_model=settings.LLM_GENERATION_MODEL)
        micro_summarizer = GeminiSummarizer(generation_model=settings.LLM_GENERATION_MODEL)
        chunker = langchain_chunker
    else:
        # Fallback to mock clients
        embedding_client = MockEmbeddingClient()
        macro_summarizer = MockSummarizer()
        micro_summarizer = MockSummarizer()
        chunker = mock_chunker
    
    return IngestionService(
        session=session,
        chunker=chunker,
        macro_summarizer=macro_summarizer,
        micro_summarizer=micro_summarizer,
        embedding_client=embedding_client,
    )
