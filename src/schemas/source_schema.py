from pydantic import BaseModel, Field

class ScanRequest(BaseModel):
    """
    GitHub 리포지토리 스캔 요청 DTO
    """
    repo_name: str = Field(
        ..., 
        description="스캔할 GitHub 리포지토리 이름 (예: 'org/repo')",
        examples=["my-org/my-project"]
    )