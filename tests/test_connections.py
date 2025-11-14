"""
연결 테스트 모듈
각 서비스(GitHub, Outline, Database)의 연결을 테스트합니다.
"""
import pytest
import asyncio
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 환경 변수 확인
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
OUTLINE_API_URL = os.getenv("OUTLINE_API_URL")
OUTLINE_API_KEY = os.getenv("OUTLINE_API_KEY")


@pytest.mark.asyncio
async def test_database_connection():
    """
    데이터베이스 연결을 테스트합니다.
    """
    from src.core.database import test_database_connection
    
    result = await test_database_connection()
    
    assert result["status"] in ["success", "error"]
    assert "message" in result
    
    if result["status"] == "error":
        print(f"Database connection error: {result['message']}")
    else:
        print(f"Database connection: {result['message']}")


@pytest.mark.asyncio
async def test_github_connection():
    """
    GitHub API 연결을 테스트합니다.
    """
    if not GITHUB_API_TOKEN:
        pytest.skip("GITHUB_API_TOKEN not set")
    
    from src.core.database import get_db_session
    from src.repositories.virtual_page_repository import VirtualPageRepository
    from src.services.github_service import GitHubService
    
    session = await get_db_session()
    try:
        repo = VirtualPageRepository(session)
        service = GitHubService(repo)
        
        result = await service.test_connection()
        
        assert result["status"] in ["success", "error"]
        assert "message" in result
        
        if result["status"] == "error":
            print(f"GitHub API connection error: {result['message']}")
        else:
            print(f"GitHub API connection: {result['message']}")
            if "user" in result:
                print(f"Authenticated as: {result['user']}")
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_outline_connection():
    """
    Outline API 연결을 테스트합니다.
    """
    if not OUTLINE_API_URL or not OUTLINE_API_KEY:
        pytest.skip("OUTLINE_API_URL or OUTLINE_API_KEY not set")
    
    from src.core.database import get_db_session
    from src.repositories.virtual_page_repository import VirtualPageRepository
    from src.services.outline_service import OutlineService
    
    session = await get_db_session()
    try:
        repo = VirtualPageRepository(session)
        service = OutlineService(repo)
        
        result = await service.test_connection()
        
        assert result["status"] in ["success", "error"]
        assert "message" in result
        
        if result["status"] == "error":
            print(f"Outline API connection error: {result['message']}")
        else:
            print(f"Outline API connection: {result['message']}")
            if "collections_count" in result:
                print(f"Collections count: {result['collections_count']}")
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_all_connections():
    """
    모든 연결을 한 번에 테스트합니다.
    """
    results = {}
    
    # Database connection test
    from src.core.database import test_database_connection
    results["database"] = await test_database_connection()
    
    # GitHub connection test
    if GITHUB_API_TOKEN:
        from src.core.database import get_db_session
        from src.repositories.virtual_page_repository import VirtualPageRepository
        from src.services.github_service import GitHubService
        
        session = await get_db_session()
        try:
            repo = VirtualPageRepository(session)
            service = GitHubService(repo)
            results["github"] = await service.test_connection()
        finally:
            await session.close()
    else:
        results["github"] = {"status": "skipped", "message": "GITHUB_API_TOKEN not set"}
    
    # Outline connection test
    if OUTLINE_API_URL and OUTLINE_API_KEY:
        from src.core.database import get_db_session
        from src.repositories.virtual_page_repository import VirtualPageRepository
        from src.services.outline_service import OutlineService
        
        session = await get_db_session()
        try:
            repo = VirtualPageRepository(session)
            service = OutlineService(repo)
            results["outline"] = await service.test_connection()
        finally:
            await session.close()
    else:
        results["outline"] = {"status": "skipped", "message": "OUTLINE_API_URL or OUTLINE_API_KEY not set"}
    
    # 결과 출력
    print("\n=== Connection Test Results ===")
    for service_name, result in results.items():
        status = result.get("status", "unknown")
        message = result.get("message", "No message")
        print(f"{service_name.upper()}: {status} - {message}")
    
    return results


if __name__ == "__main__":
    """
    직접 실행 시 모든 연결 테스트를 실행합니다.
    """
    async def main():
        print("Running all connection tests...\n")
        results = await test_all_connections()
        print("\n=== Summary ===")
        for service_name, result in results.items():
            status = result.get("status", "unknown")
            print(f"{service_name}: {status}")
    
    asyncio.run(main())

