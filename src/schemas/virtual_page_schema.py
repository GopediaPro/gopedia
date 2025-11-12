import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

from src.schemas.anchor_schema import AnchorRead # Anchor 정보 포함용

# 기본 Pydantic 모델
class VirtualPageBase(BaseModel):
    title: Optional[str] = None
    content_summary: Optional[str] = None
    content_description: Optional[str] = None
    outline_document_id: Optional[str] = None

# 데이터 생성 시 사용 (Anchor ID 필요)
class VirtualPageCreate(VirtualPageBase):
    anchor_id: uuid.UUID

# 데이터 수정 시 사용 (예: Outline ID 업데이트)
class VirtualPageUpdate(BaseModel):
    outline_document_id: str

# 데이터 조회 시 사용 (Read)
class VirtualPageRead(VirtualPageBase):
    id: uuid.UUID
    anchor_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    # Anchor 정보도 함께 반환
    anchor: AnchorRead 

    model_config = ConfigDict(from_attributes=True)