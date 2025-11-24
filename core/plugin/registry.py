from typing import Dict
from app.config import settings
from core.plugin.interface import PluginClientInterface
from core.plugin.client import GrpcPluginClient

class PluginRegistry:
    """
    Singleton Plugin Manager.
    앱 시작 시 .env에 정의된 플러그인들과 연결을 맺고 캐싱합니다.
    """
    _clients: Dict[str, PluginClientInterface] = {}

    @classmethod
    async def initialize(cls):
        """설정된 모든 플러그인에 대해 연결 초기화"""
        # settings.PLUGIN_REGISTRY 예시: {"jira": "localhost:50051", "ai": "ai-service:50052"}
        for name, address in settings.PLUGIN_REGISTRY.items():
            client = GrpcPluginClient()
            await client.connect(address)
            cls._clients[name] = client

    @classmethod
    def get_client(cls, plugin_name: str) -> PluginClientInterface:
        client = cls._clients.get(plugin_name)
        if not client:
            raise ValueError(f"Plugin '{plugin_name}' not found in registry.")
        return client

    @classmethod
    async def shutdown(cls):
        """연결 종료"""
        for client in cls._clients.values():
            await client.close()