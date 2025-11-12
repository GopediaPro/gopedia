from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.publish_schema import PublishRequest, PublishResponse
from src.services.outline_service import OutlineService
from src.repositories.virtual_page_repository import VirtualPageRepository

router = APIRouter(
    prefix="/publish",
    tags=["Publishing"]
)

# --- 서비스 의존성 주입 ---
# (source_controller.py의 get_virtual_page_repo를 재사용하거나 여기서 정의)
def get_virtual_page_repo(db: AsyncSession = Depends(get_db)) -> VirtualPageRepository:
    return VirtualPageRepository(db)

def get_outline_service(repo: VirtualPageRepository = Depends(get_virtual_page_repo)) -> OutlineService:
    """OutlineService 의존성"""
    return OutlineService(repo)
# ---

@router.post("/outline", response_model=PublishResponse)
async def publish_to_outline(
    request: PublishRequest,
    service: OutlineService = Depends(get_outline_service)
):
    """
    VirtualPage를 Outline 서비스에 발행(생성)합니다.
    """
    try:
        doc_id = await service.publish_page(request.page_id, request.collection_id)
        
        return PublishResponse(
            page_id=request.page_id,
            outline_document_id=doc_id,
            status="published" # 또는 업데이트 시 "updated"
        )
        
    except ValueError as e:
        # 서비스에서 페이지를 못 찾은 경우 등
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Outline API 오류 등
        raise HTTPException(status_code=500, detail=f"Outline 발행 실패: {str(e)}")