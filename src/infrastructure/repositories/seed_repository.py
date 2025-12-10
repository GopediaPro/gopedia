"""
Seed Repository

Repository layer for database operations related to seeding.
"""
from typing import Optional
import hashlib
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import SysDict, BlobStore


class SeedRepository:
    """Repository for seeding-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_or_create_sys_dict(self, category: str, val: str) -> SysDict:
        """Get or create a SysDict entry."""
        stmt = select(SysDict).where(SysDict.category == category, SysDict.val == val)
        result = await self.session.execute(stmt)
        obj = result.scalar_one_or_none()
        
        if not obj:
            obj = SysDict(category=category, val=val)
            self.session.add(obj)
            await self.session.flush()
            print(f"  Created SysDict: {category}.{val} (id={obj.id})")
        return obj
    
    async def create_or_get_blob(self, content: str, content_type: str = "text/markdown") -> str:
        """Create or get a blob store entry. Returns the hash."""
        content_bytes = content.encode('utf-8')
        sha256_hash = hashlib.sha256(content_bytes).hexdigest()
        
        stmt = select(BlobStore).where(BlobStore.hash == sha256_hash)
        result = await self.session.execute(stmt)
        if not result.scalar_one_or_none():
            blob = BlobStore(
                hash=sha256_hash,
                body=content_bytes,
                content_type=content_type
            )
            self.session.add(blob)
            await self.session.flush()
            print(f"  Created Blob: {sha256_hash[:8]}...")
        
        return sha256_hash
