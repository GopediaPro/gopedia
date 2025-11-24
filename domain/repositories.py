from abc import ABC, abstractmethod
from typing import Optional, List
from domain.entities.models import OriginData, Revision, KnowledgeEdge

class RhizomeRepository(ABC):
    """
    만물 통합 저장소(Rhizome) 접근을 위한 추상 인터페이스.
    구현체는 core/db/sql_repository.py 에서 SQLAlchemy를 사용해 구현됩니다.
    """

    @abstractmethod
    async def save_origin(self, origin: OriginData) -> OriginData:
        """OriginData 생성 또는 업데이트 (Upsert)"""
        pass

    @abstractmethod
    async def get_by_urn(self, urn: str) -> Optional[OriginData]:
        """Global Identifier로 데이터 조회"""
        pass

    @abstractmethod
    async def append_revision(self, origin_id: int, revision: Revision) -> Revision:
        """새로운 리비전을 추가하고 OriginData의 포인터를 갱신"""
        pass

    @abstractmethod
    async def get_graph_neighbors(self, origin_id: int, depth: int = 1) -> List[KnowledgeEdge]:
        """특정 노드 주변의 맥락(Edges) 조회"""
        pass