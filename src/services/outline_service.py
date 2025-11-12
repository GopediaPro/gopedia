import httpx
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.virtual_page_repository import VirtualPageRepository
from src.core.config import settings

class OutlineService:
    
    def __init__(self, repo: VirtualPageRepository):
        self.repository = repo
        self.api_url = settings.OUTLINE_API_URL
        self.api_key = settings.OUTLINE_API_KEY
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    async def publish_page(self, page_id: uuid.UUID, collection_id: str) -> str:
        """
        VirtualPage를 Outline에 발행(생성)합니다.
        """
        # 1. DB에서 VirtualPage 정보 가져오기
        page = await self.repository.get_virtual_page(page_id)
        
        if not page:
            raise ValueError(f"VirtualPage not found: {page_id}")
            
        # 2. 이미 발행되었는지 확인
        if page.outline_document_id:
            print(f"Page {page_id} is already published (Doc ID: {page.outline_document_id}).")
            # (2단계: 업데이트 로직 구현)
            # 여기서는 기존 ID 반환
            return page.outline_document_id

        # 3. Outline API로 보낼 내용 준비
        title = page.title or "Untitled"
        # 내용: Summary > Description > (Anchor Locator)
        text = page.content_summary or page.content_description or f"Anchor: {page.anchor.locator}"

        # 4. Outline API 호출 (문서 생성)
        try:
            new_doc_id = await self.create_document_api(title, collection_id, text)
        except Exception as e:
            print(f"Failed to create document in Outline: {e}")
            raise

        # 5. DB에 Outline ID 업데이트
        await self.repository.update_page_outline_id(page_id, new_doc_id)
        
        return new_doc_id

    async def create_document_api(self, title: str, collection_id: str, text: str = "") -> str:
        """
        Outline /api/documents.create API를 호출합니다.
        """
        api_endpoint = f"{self.api_url}/api/documents.create"
        payload = {
            "title": title,
            "text": text,
            "collectionId": collection_id,
            "publish": True # 생성 즉시 발행
        }

        async with httpx.AsyncClient(headers=self.headers, http2=True) as client:
            try:
                response = await client.post(api_endpoint, json=payload)
                response.raise_for_status() # API 오류 시 예외 발생
                
                data = response.json()
                
                if data and data.get("data") and data.get("data").get("id"):
                    doc_id = data["data"]["id"]
                    print(f"Successfully created Outline document: {doc_id}")
                    return doc_id
                else:
                    raise Exception(f"Invalid response from Outline API: {data}")
                    
            except httpx.HTTPStatusError as e:
                print(f"Outline API Error: {e.response.status_code} - {e.response.text}")
                raise
            except Exception as e:
                raise