import httpx
import asyncio
import base64
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.base_source_service import BaseSourceService
from src.repositories.virtual_page_repository import VirtualPageRepository
from src.schemas.anchor_schema import AnchorCreate
from src.schemas.virtual_page_schema import VirtualPageCreate
from src.models.models import AnchorType
from src.core.config import settings

class GitHubService(BaseSourceService):
    
    def __init__(self, repo: VirtualPageRepository):
        self.repository = repo
        self.github_token = settings.GITHUB_API_TOKEN
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.github_token}"
        }

    async def scan(self, repo_name: str, **kwargs) -> dict:
        """
        GitHub 리포지토리 전체를 스캔합니다.
        """
        # (실제 구현) httpx.AsyncClient를 사용하여 GitHub Contents API 호출
        # 예: /repos/{repo_name}/contents
        
        # 여기서는 비동기 처리를 보여주기 위한 목업(mock) 데이터를 사용합니다.
        print(f"Scanning repo: {repo_name}")
        
        async with httpx.AsyncClient(headers=self.headers, http2=True) as client:
            try:
                # 리포지토리 루트 컨텐츠 가져오기
                root_items = await self._fetch_github_contents(client, repo_name, "")
                
                # 병렬 처리
                tasks = [
                    self.process_item(item, repo_name, client) for item in root_items
                ]
                await asyncio.gather(*tasks)

            except httpx.HTTPStatusError as e:
                print(f"Error scanning GitHub repo {repo_name}: {e}")
                return {"status": "error", "message": str(e)}

        print(f"Finished scanning repo: {repo_name}")
        return {"status": "scan_started", "repo": repo_name}

    async def _fetch_github_contents(self, client: httpx.AsyncClient, repo_name: str, path: str) -> List[Dict[str, Any]]:
        """Helper: GitHub Contents API 호출"""
        url = f"https://api.github.com/repos/{repo_name}/contents/{path}"
        response = await client.get(url)
        response.raise_for_status() # 오류 시 예외 발생
        return response.json()

    async def process_item(self, item: Dict[str, Any], repo_name: str, client: httpx.AsyncClient):
        """
        GitHub 아이템(파일 또는 디렉터리)을 처리합니다.
        디렉터리인 경우 재귀적으로 스캔합니다.
        """
        item_type = item.get("type")
        item_path = item.get("path")
        item_sha = item.get("sha")
        
        if not item_path:
            return

        # 1. Locator 생성
        locator = f"github:{repo_name}/{item_path}"

        # 2. Anchor가 이미 존재하는지 확인 (sha 비교 포함)
        existing_anchor = await self.repository.find_anchor_by_locator(locator)
        
        if existing_anchor:
            if existing_anchor.origin_id == item_sha:
                # print(f"Skipping (unchanged): {locator}")
                return # 변경 사항 없음
            else:
                # (2단계: 업데이트 로직)
                # print(f"Updating: {locator}")
                existing_anchor.origin_id = item_sha
                # ... 메타데이터 업데이트 ...
                await self.repository.db.commit()
        else:
            # 3. Anchor가 없는 경우 (신규 생성)
            print(f"Creating new Anchor/Page for: {locator}")
            
            # Anchor 데이터 준비
            anchor_data = AnchorCreate(
                type=AnchorType.GITHUB,
                locator=locator,
                origin_id=item_sha,
                metadata={"type": item_type, "size": item.get("size"), "url": item.get("html_url")}
            )
            
            try:
                # 4. Anchor 생성
                new_anchor = await self.repository.create_anchor(anchor_data)

                # 5. VirtualPage 데이터 준비 (파일인 경우 내용 일부 가져오기)
                title = item.get("name")
                description = None

                if item_type == "file" and item.get("size", 0) > 0:
                     # (개선) 파일 내용을 가져와서 description에 넣을 수 있음
                     # 예: README.md인 경우
                     if title.lower() == "readme.md":
                         description = await self._fetch_file_content(client, repo_name, item_path)
                
                page_data = VirtualPageCreate(
                    anchor_id=new_anchor.id,
                    title=title,
                    content_description=description
                )
                
                # 6. VirtualPage 생성
                await self.repository.create_virtual_page(page_data)
            
            except Exception as e:
                # (중요) 동시성 문제나 유니크 제약 조건 위반 시 롤백
                print(f"Error processing item {locator}: {e}")
                await self.repository.db.rollback()


        # 7. 디렉터리인 경우 재귀 호출
        if item_type == "dir":
            try:
                sub_items = await self._fetch_github_contents(client, repo_name, item_path)
                tasks = [self.process_item(sub_item, repo_name, client) for sub_item in sub_items]
                await asyncio.gather(*tasks)
            except httpx.HTTPStatusError as e:
                print(f"Error fetching directory contents {item_path}: {e}")


    async def _fetch_file_content(self, client: httpx.AsyncClient, repo_name: str, path: str) -> str | None:
        """Helper: GitHub 파일 내용 (Base64) 가져오기 (README용)"""
        try:
            url = f"https://api.github.com/repos/{repo_name}/contents/{path}"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data.get("encoding") == "base64" and data.get("content"):
                content = base64.b64decode(data["content"]).decode("utf-8")
                return content
        except Exception as e:
            print(f"Error fetching file content {path}: {e}")
        return None