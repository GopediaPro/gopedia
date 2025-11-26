from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from uuid import UUID

from src.domain.entities import OriginData, KnowledgeEdge, TreeNode

class RhizomeRepository(ABC):
    """
    Abstract Base Class for Rhizome Core Data Operations.
    This enforces the Hexagonal Architecture by defining the port 
    that the persistence adapter must implement.
    """

    @abstractmethod
    async def save(self, entity: OriginData) -> OriginData:
        """Persist an OriginData entity."""
        pass

    @abstractmethod
    async def get_by_urn(self, urn: str) -> Optional[OriginData]:
        """Retrieve OriginData by its unique URN."""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[OriginData]:
        """Retrieve OriginData by its internal ID."""
        pass

    @abstractmethod
    async def find_graph_neighbors(
        self, 
        node_id: int, 
        predicate_filter: Optional[List[str]] = None,
        depth: int = 1
    ) -> List[KnowledgeEdge]:
        """
        Find neighboring nodes in the knowledge graph.
        
        Args:
            node_id: The ID of the starting node.
            predicate_filter: Optional list of predicate names to filter edges.
            depth: Traversal depth (default 1).
        """
        pass

    @abstractmethod
    async def get_tree_structure(self, root_id: int) -> TreeNode:
        """Retrieve the visualization tree structure starting from a root."""
        pass
