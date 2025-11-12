import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.virtual_page_schema import VirtualPageRead
from src.schemas.anchor_schema import AnchorRead
from src.repositories.virtual_page_repository import VirtualPageRepository

router = APIRouter(
    prefix="/virtual-pages",
    tags=["Virtual Pages"]
)

# --- 리포지토리 의존성 주입 ---
def get_virtual_page_repo(db: AsyncSession = Depends(get_db)) -> VirtualPageRepository:
    return VirtualPageRepository(db)
# ---

@router.get("/{page_id}", response_model=VirtualPageRead)
async def get_virtual_page_by_id(
    page_id: uuid.UUID,
    repo: VirtualPageRepository = Depends(get_virtual_page_repo)
):
    """
    ID로 VirtualPage 상세 정보 조회 (Anchor 정보 포함)
    """
    page = await repo.get_virtual_page(page_id)
    if not page:
        raise HTTPException(status_code=404, detail="VirtualPage not found")
    return page

# Anchor 조회를 별도 컨트롤러/태그로 분리할 수도 있음
@router.get("/anchor/by-locator", response_model=AnchorRead, tags=["Anchors"])
async def get_anchor_by_locator(
    locator: str = Query(..., description="예: 'github:org/repo/path/file.md'"),
    repo: VirtualPageRepository = Depends(get_virtual_page_repo)
):
    """
    Locator 문자열로 Anchor 정보 조회
    (VirtualPage 정보는 포함하지 않음)
    """
    anchor = await repo.find_anchor_by_locator(locator)
    if not anchor:
        raise HTTPException(status_code=404, detail="Anchor not found")
    return anchor