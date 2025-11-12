import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.models.models import Anchor, VirtualPage
from src.schemas.anchor_schema import AnchorCreate
from src.schemas.virtual_page_schema import VirtualPageCreate

# BaseRepository를 상속하는 대신, MVP에서는 필요한 메서드만 직접 구현
class VirtualPageRepository:
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_anchor_by_locator(self, locator: str) -> Anchor | None:
        """
        Locator 문자열로 Anchor를 찾습니다.
        """
        statement = select(Anchor).where(Anchor.locator == locator)
        result = await self.db.execute(statement)
        return result.scalars().first()

    async def get_virtual_page(self, page_id: uuid.UUID) -> VirtualPage | None:
        """
        ID로 VirtualPage를 찾습니다. (Anchor 정보 포함)
        """
        statement = (
            select(VirtualPage)
            .where(VirtualPage.id == page_id)
            .options(selectinload(VirtualPage.anchor)) # Anchor Eager Loading
        )
        result = await self.db.execute(statement)
        return result.scalars().first()

    async def create_anchor(self, anchor_data: AnchorCreate) -> Anchor:
        """
        새로운 Anchor를 생성합니다.
        """
        db_anchor = Anchor(**anchor_data.model_dump())
        self.db.add(db_anchor)
        await self.db.commit()
        await self.db.refresh(db_anchor)
        return db_anchor

    async def create_virtual_page(self, page_data: VirtualPageCreate) -> VirtualPage:
        """
        새로운 VirtualPage를 생성합니다. (Anchor가 먼저 생성되어야 함)
        """
        db_page = VirtualPage(**page_data.model_dump())
        self.db.add(db_page)
        await self.db.commit()
        await self.db.refresh(db_page)
        return db_page

    async def update_page_outline_id(self, page_id: uuid.UUID, outline_id: str) -> VirtualPage | None:
        """
        VirtualPage의 outline_document_id를 업데이트합니다.
        """
        db_page = await self.get_virtual_page(page_id) # 먼저 조회
        if db_page:
            db_page.outline_document_id = outline_id
            await self.db.commit()
            await self.db.refresh(db_page)
        return db_page

# --- 리포지토리 의존성 주입 ---
# FastAPI의 Depends와 함께 사용하기 위해,
# 세션을 주입받아 리포지토리 인스턴스를 반환하는 함수를 정의합니다.
# (또는 컨트롤러에서 get_db를 통해 세션을 받고 직접 인스턴스화)

# 예: 컨트롤러에서 사용하는 방식
# from src.core.database import get_db
# @router.post("/")
# async def create_page(db: AsyncSession = Depends(get_db)):
#     repo = VirtualPageRepository(db)
#     ...