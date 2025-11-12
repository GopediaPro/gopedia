from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.schemas.source_schema import ScanRequest
from src.services.github_service import GitHubService
from src.repositories.virtual_page_repository import VirtualPageRepository

router = APIRouter(
    prefix="/sources",
    tags=["Sources"]
)

# --- 서비스 의존성 주입 ---
# 리포지토리를 생성하고, 리포지토리를 서비스에 주입합니다.

def get_virtual_page_repo(db: AsyncSession = Depends(get_db)) -> VirtualPageRepository:
    """VirtualPageRepository 의존성"""
    return VirtualPageRepository(db)

def get_github_service(repo: VirtualPageRepository = Depends(get_virtual_page_repo)) -> GitHubService:
    """GitHubService 의존성"""
    return GitHubService(repo)
# ---

@router.post("/github/scan", status_code=202) # 202 Accepted (백그라운드 작업)
async def scan_github_repo(
    request: ScanRequest,
    background_tasks: BackgroundTasks, # 백그라운드 작업 주입
    service: GitHubService = Depends(get_github_service)
):
    """
    GitHub 리포지토리 스캔을 트리거합니다.
    (주의) 실제 스캔은 오래 걸릴 수 있으므로 백그라운드 작업으로 실행합니다.
    """
    try:
        # service.scan은 비동기 함수이므로 background_tasks.add_task가
        # awaitable을 직접 실행하도록 합니다.
        background_tasks.add_task(service.scan, request.repo_name)
        
        return {"status": "scan_started", "repo": request.repo_name}
    
    except Exception as e:
        # (실제로는 Background Task 내부의 예외는 여기로 잡히지 않음)
        # Background Task의 예외 처리는 해당 작업 내에서 별도 로깅/처리 필요
        raise HTTPException(status_code=500, detail=str(e))