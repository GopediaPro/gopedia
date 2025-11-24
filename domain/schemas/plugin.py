from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from enum import Enum

class PluginType(str, Enum):
    CONNECTOR = "connector"  # 외부 데이터 수집 (Source -> Gopedia)
    CREATOR = "creator"      # 데이터 가공/생성 (Gopedia -> AI/Calc -> Gopedia)

class PluginPayload(BaseModel):
    """
    Universal Payload Envelope.
    Core는 이 Payload를 Plugin에게 던지고, Plugin은 이를 해석해 로직을 수행합니다.
    """
    context_urn: Optional[str] = Field(None, description="작업 대상 Origin URN")
    operation: str = Field(..., description="플러그인이 수행해야 할 명령 (e.g., 'fetch_issues', 'summarize')")
    params: Dict[str, Any] = Field(default_factory=dict, description="명령 수행에 필요한 파라미터")
    data_snapshot: Optional[Dict[str, Any]] = Field(None, description="처리할 원본 데이터 (Creator용)")

class PluginResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None # 결과 데이터 (JSON)
    error_message: Optional[str] = None