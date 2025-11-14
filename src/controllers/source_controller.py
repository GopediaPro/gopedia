from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db, get_db_session
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

async def _scan_github_repo_background(repo_name: str):
    """
    백그라운드 태스크에서 실행되는 GitHub 리포지토리 스캔 함수.
    별도의 세션을 생성하여 사용합니다.
    """
    session = await get_db_session()
    try:
        repo = VirtualPageRepository(session)
        service = GitHubService(repo)
        await service.scan(repo_name)
    except Exception as e:
        print(f"Error in background scan task: {e}")
        await session.rollback()
        raise
    finally:
        await session.close()

@router.post("/github/scan", status_code=202) # 202 Accepted (백그라운드 작업)
async def scan_github_repo(
    request: ScanRequest,
    background_tasks: BackgroundTasks, # 백그라운드 작업 주입
):
    """
    GitHub 리포지토리 스캔을 트리거합니다.
    (주의) 실제 스캔은 오래 걸릴 수 있으므로 백그라운드 작업으로 실행합니다.
    """
    try:
        # 백그라운드 태스크에서 별도의 세션을 생성하여 사용
        background_tasks.add_task(_scan_github_repo_background, request.repo_name)
        
        return {"status": "scan_started", "repo": request.repo_name}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))