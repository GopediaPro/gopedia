from typing import List, Optional
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories import RhizomeRepository
from src.domain.entities import OriginData, KnowledgeEdge, TreeNode, SysDict

class SqlAlchemyRhizomeRepository(RhizomeRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, entity: OriginData) -> OriginData:
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def get_by_urn(self, urn: str) -> Optional[OriginData]:
        stmt = select(OriginData).where(OriginData.urn == urn).options(
            selectinload(OriginData.revisions)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, id: int) -> Optional[OriginData]:
        stmt = select(OriginData).where(OriginData.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_graph_neighbors(
        self, 
        node_id: int, 
        predicate_filter: Optional[List[str]] = None,
        depth: int = 1
    ) -> List[KnowledgeEdge]:
        # Simple implementation for depth=1
        stmt = select(KnowledgeEdge).where(KnowledgeEdge.source_id == node_id)
        
        if predicate_filter:
            # Join with SysDict to filter by predicate val (name)
            stmt = stmt.join(KnowledgeEdge.predicate).where(SysDict.val.in_(predicate_filter))
            
        stmt = stmt.options(selectinload(KnowledgeEdge.target))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_tree_structure(self, root_id: int) -> TreeNode:
        # Recursive query might be needed for full tree, but for now return the node with children loaded
        stmt = select(TreeNode).where(TreeNode.id == root_id).options(
            selectinload(TreeNode.children)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
