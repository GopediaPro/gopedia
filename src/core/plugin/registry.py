import json
from src.core.plugin.adapter import PluginClientInterface, PluginRequest, PluginResult

class PluginRegistry:
    """
    Manages active plugin connections.
    """
    def __init__(self):
        self._clients: Dict[str, PluginClientInterface] = {}

    async def register_plugin(self, name: str, target: str) -> None:
        # TODO: Implement API client registration
        print(f"Registered plugin '{name}' at {target} (Placeholder)")
        pass

    def get_client(self, name: str) -> Optional[PluginClientInterface]:
        return self._clients.get(name)

    async def close_all(self) -> None:
        for client in self._clients.values():
            await client.close()
        self._clients.clear()

# Global Registry Instance
plugin_registry = PluginRegistry()
