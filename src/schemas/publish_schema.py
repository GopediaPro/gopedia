import uuid
from pydantic import BaseModel, Field

class PublishRequest(BaseModel):
    """
    Outline 발행 요청 DTO
    """
    page_id: uuid.UUID = Field(..., description="발행할 VirtualPage의 ID")
    collection_id: str = Field(..., description="발행할 Outline 컬렉션의 ID")

class PublishResponse(BaseModel):
    """
    Outline 발행 응답 DTO
    """
    page_id: uuid.UUID
    outline_document_id: str
    status: str = "published"