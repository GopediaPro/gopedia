from abc import ABC, abstractmethod

class BaseSourceService(ABC):
    """
    다양한 소스(GitHub, Filesystem 등)를 스캔하기 위한 추상 기본 클래스
    """

    @abstractmethod
    async def scan(self, target_id: str, **kwargs) -> dict:
        """
        지정된 타겟(예: repo_name)을 스캔하여 데이터를 처리합니다.
        """
        raise NotImplementedError