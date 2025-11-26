from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Data Transfer Objects (DTOs)
# -----------------------------------------------------------------------------

class PluginRequest(BaseModel):
    """Standardized request payload for all plugins."""
    action: str = Field(..., description="The action to perform (e.g., 'ingest', 'process')")
    payload: Dict[str, Any] = Field(..., description="The actual data payload")
    context: Dict[str, Any] = Field(default_factory=dict, description="Trace context or metadata")

class PluginResult(BaseModel):
    """Standardized result from plugins."""
    status: str = Field(..., description="'success' or 'error'")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data if success")
    error_message: Optional[str] = Field(None, description="Error message if failure")

# -----------------------------------------------------------------------------
# Plugin Client Interface (Port)
# -----------------------------------------------------------------------------

class PluginClientInterface(ABC):
    """
    Abstract Adapter for communicating with external plugins.
    This isolates the core domain from specific implementation details.
    """

    @abstractmethod
    async def connect(self, target: str) -> None:
        """Establish connection to the service."""
        pass

    @abstractmethod
    async def execute(self, request: PluginRequest) -> PluginResult:
        """
        Execute a command on the remote plugin.
        
        Args:
            request: The standardized request object.
            
        Returns:
            PluginResult: The standardized result object.
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the connection."""
        pass
