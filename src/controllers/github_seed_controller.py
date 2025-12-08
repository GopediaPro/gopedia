"""
GitHub Seed Controller

Controller layer for GitHub repository seeding (CLI and FastAPI).
"""
import asyncio
import sys
import os
import argparse
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import AsyncSessionLocal, get_db
from src.infrastructure.external.github_client import GitHubClient
from src.services.github_seed_service import GitHubSeedService
from src.core.config import settings


# ============================================================================
# Pydantic Models for FastAPI
# ============================================================================

class SeedRequest(BaseModel):
    """Request model for GitHub repository seeding."""
    owner: str = Field(..., description="GitHub repository owner")
    repo: str = Field(..., description="GitHub repository name")
    branch: Optional[str] = Field(default=None, description="Branch name (default: main)")
    token: Optional[str] = Field(default=None, description="GitHub personal access token (optional)")


class SeedResponse(BaseModel):
    """Response model for GitHub repository seeding."""
    success: bool = Field(..., description="Whether the seeding was successful")
    message: str = Field(..., description="Response message")
    files_processed: Optional[int] = Field(default=None, description="Number of files processed")


# ============================================================================
# Controller Class
# ============================================================================

class GitHubSeedController:
    """Controller for GitHub repository seeding operations."""
    
    @staticmethod
    async def run(
        owner: Optional[str] = None,
        repo: Optional[str] = None,
        branch: Optional[str] = None,
        token: Optional[str] = None,
        session: Optional[AsyncSession] = None
    ) -> int:
        """
        Execute GitHub repository seeding.
        
        Args:
            owner: GitHub repository owner
            repo: GitHub repository name
            branch: Branch name (default: main)
            token: GitHub personal access token
            session: Optional database session (if None, creates a new one)
        
        Returns:
            Number of files processed
        """
        # Use provided values or fall back to settings
        owner = owner or settings.GITHUB_OWNER
        repo = repo or settings.GITHUB_REPO
        branch = branch or settings.GITHUB_BRANCH
        token = token or settings.GITHUB_TOKEN
        
        # Validate required arguments
        if not owner:
            raise ValueError("owner is required. Set GITHUB_OWNER in .env file or provide owner argument.")
        
        if not repo:
            raise ValueError("repo is required. Set GITHUB_REPO in .env file or provide repo argument.")
        
        # Use provided session or create a new one
        if session:
            # Use provided session (for FastAPI dependency injection)
            github_client = GitHubClient(token=token)
            seed_service = GitHubSeedService(session, github_client)
            return await seed_service.seed_repository(
                owner=owner,
                repo=repo,
                branch=branch
            )
        else:
            # Create new session (for CLI)
            async with AsyncSessionLocal() as new_session:
                github_client = GitHubClient(token=token)
                seed_service = GitHubSeedService(new_session, github_client)
                return await seed_service.seed_repository(
                    owner=owner,
                    repo=repo,
                    branch=branch
                )


# ============================================================================
# FastAPI Router
# ============================================================================

router = APIRouter(prefix="/api/github", tags=["github"])


@router.post("/seed", response_model=SeedResponse, status_code=status.HTTP_200_OK)
async def seed_repository(
    request: SeedRequest,
    session: AsyncSession = Depends(get_db)
) -> SeedResponse:
    """
    Seed database with GitHub repository data.
    
    This endpoint fetches file information from a GitHub repository and creates
    mock data in the database following the Rhizome architecture.
    
    Args:
        request: Seed request containing owner, repo, branch, and optional token
        session: Database session (injected by FastAPI)
    
    Returns:
        SeedResponse with success status and number of files processed
    
    Raises:
        HTTPException: If seeding fails or required parameters are missing
    """
    try:
        files_processed = await GitHubSeedController.run(
            owner=request.owner,
            repo=request.repo,
            branch=request.branch,
            token=request.token,
            session=session
        )
        
        return SeedResponse(
            success=True,
            message=f"Successfully seeded repository {request.owner}/{request.repo}",
            files_processed=files_processed
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed repository: {str(e)}"
        )


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """CLI entry point for GitHub repository seeding."""
    parser = argparse.ArgumentParser(
        description="Seed database with GitHub repository data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use values from .env file
  python scripts/seed_github_mock_data.py
  
  # Override specific values
  python scripts/seed_github_mock_data.py --owner octocat --repo Hello-World
  
  # Use custom token
  python scripts/seed_github_mock_data.py --token <your_token>
        """
    )
    parser.add_argument(
        "--owner", 
        default=settings.GITHUB_OWNER,
        help=f"GitHub repository owner (default: from GITHUB_OWNER env var or {settings.GITHUB_OWNER})"
    )
    parser.add_argument(
        "--repo", 
        default=settings.GITHUB_REPO,
        help=f"GitHub repository name (default: from GITHUB_REPO env var or {settings.GITHUB_REPO})"
    )
    parser.add_argument(
        "--branch", 
        default=settings.GITHUB_BRANCH,
        help=f"Branch name (default: from GITHUB_BRANCH env var or {settings.GITHUB_BRANCH})"
    )
    parser.add_argument(
        "--token", 
        default=settings.GITHUB_TOKEN,
        help="GitHub personal access token (default: from GITHUB_TOKEN env var, optional, for rate limits)"
    )
    
    args = parser.parse_args()
    
    try:
        files_processed = asyncio.run(
            GitHubSeedController.run(
                owner=args.owner,
                repo=args.repo,
                branch=args.branch,
                token=args.token
            )
        )
        print(f"\n✓ Successfully processed {files_processed} files")
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
