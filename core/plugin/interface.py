from abc import ABC, abstractmethod
from domain.schemas.plugin import PluginPayload, PluginResult

class PluginClientInterface(ABC):
    """
    외부 gRPC 플러그인과의 통신을 추상화하는 어댑터.
    """
    
    @abstractmethod
    async def connect(self, service_address: str) -> None:
        """gRPC 채널 연결 (Lazy Connection 권장)"""
        pass

    @abstractmethod
    async def execute(self, payload: PluginPayload) -> PluginResult:
        """
        범용 실행 메서드.
        Core는 구체적인 RPC 메서드(Stub)를 몰라도 이 메서드를 통해 요청을 보냅니다.
        내부 구현체에서 gRPC Stub의 적절한 메서드(e.g., Ingest(), Process())를 호출합니다.
        """
        pass
        
    @abstractmethod
    async def close(self):
        """리소스 정리"""
        pass