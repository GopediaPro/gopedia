import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any

from src.models.models import AnchorType # Enum 임포트

# 기본 Pydantic 모델 (공통 필드)
class AnchorBase(BaseModel):
    type: AnchorType
    locator: str
    origin_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# 데이터 생성 시 사용 (입력 DTO)
class AnchorCreate(AnchorBase):
    pass

# 데이터베이스 모델에서 Pydantic 모델로 변환 (Read)
class AnchorRead(AnchorBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    # SQLAlchemy 모델 객체를 Pydantic 모델로 자동 변환
    model_config = ConfigDict(from_attributes=True)