"""
GitHub Mock Data Seeding Script

This script fetches file information from GitHub repositories and creates
mock data in the database following the Rhizome architecture.

The script reads default values from .env file (GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH, GITHUB_TOKEN)
and allows overriding them via command-line arguments.

Usage:
    # Use values from .env file
    python scripts/seed_github_mock_data.py
    
    # Override specific values
    python scripts/seed_github_mock_data.py --owner octocat --repo Hello-World
    
    # Use custom token
    python scripts/seed_github_mock_data.py --token <your_token>
    
    # All options
    python scripts/seed_github_mock_data.py --owner <owner> --repo <repo> [--branch <branch>] [--token <token>]

Examples:
    python scripts/seed_github_mock_data.py
    python scripts/seed_github_mock_data.py --owner octocat --repo Hello-World --branch main
"""
import asyncio
import sys
import os
import argparse
import hashlib
from datetime import datetime, timezone
from uuid import uuid4
from typing import Optional, Dict, List, Tuple
import re

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import AsyncSessionLocal
from src.core.config import settings
from src.domain.entities import (
    SysDict, OriginData, Revision, BlobStore, KnowledgeEdge,
    TreeNode, ChunkNode
)


# ============================================================================
# GitHub API Client
# ============================================================================

class GitHubClient:
    """Simple GitHub API client for fetching repository file information."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
    
    async def get_repo_info(self, owner: str, repo: str) -> Dict:
        """Get repository information."""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_file_tree(self, owner: str, repo: str, branch: str = "main") -> List[Dict]:
        """Get recursive file tree from repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get("tree", [])
    
    async def get_file_content(self, owner: str, repo: str, path: str, branch: str = "main") -> Optional[str]:
        """Get file content from repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": branch}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                data = response.json()
                if data.get("type") == "file":
                    import base64
                    content = base64.b64decode(data.get("content", "")).decode("utf-8")
                    return content
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise
        return None


# ============================================================================
# Database Helper Functions
# ============================================================================

async def get_or_create_sys_dict(
    session: AsyncSession, 
    category: str, 
    val: str
) -> SysDict:
    """Get or create a SysDict entry."""
    stmt = select(SysDict).where(SysDict.category == category, SysDict.val == val)
    result = await session.execute(stmt)
    obj = result.scalar_one_or_none()
    
    if not obj:
        obj = SysDict(category=category, val=val)
        session.add(obj)
        await session.flush()
        print(f"  Created SysDict: {category}.{val} (id={obj.id})")
    return obj


async def create_blob(session: AsyncSession, content: str, content_type: str = "text/markdown") -> str:
    """Create or get a blob store entry."""
    content_bytes = content.encode('utf-8')
    sha256_hash = hashlib.sha256(content_bytes).hexdigest()
    
    stmt = select(BlobStore).where(BlobStore.hash == sha256_hash)
    result = await session.execute(stmt)
    if not result.scalar_one_or_none():
        blob = BlobStore(
            hash=sha256_hash,
            body=content_bytes,
            content_type=content_type
        )
        session.add(blob)
        await session.flush()
        print(f"  Created Blob: {sha256_hash[:8]}...")
    
    return sha256_hash


def generate_urn(dtype: str, uuid_str: Optional[str] = None) -> str:
    """Generate URN in format: urn:rhizome:<dtype>:<uuid>"""
    if uuid_str is None:
        uuid_str = str(uuid4())
    return f"urn:rhizome:{dtype}:{uuid_str}"


def slugify(name: str) -> str:
    """Convert name to URL-safe slug."""
    # Remove extension for slug
    name_without_ext = os.path.splitext(name)[0]
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', name_without_ext.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug or "untitled"


def split_path(path: str) -> Tuple[str, str]:
    """Split path into directory and filename."""
    if '/' in path:
        dir_path, filename = os.path.split(path)
        return dir_path, filename
    return "", path


# ============================================================================
# Chunk Processing
# ============================================================================

def split_into_chunks(content: str, max_chunk_size: int = 1000) -> List[Dict[str, str]]:
    """
    Split content into chunks for ChunkNode.
    Simple implementation: split by lines, then by paragraphs.
    """
    chunks = []
    lines = content.split('\n')
    current_chunk = []
    current_size = 0
    
    for line in lines:
        line_size = len(line)
        if current_size + line_size > max_chunk_size and current_chunk:
            # Save current chunk
            chunk_text = '\n'.join(current_chunk)
            chunk_type = 'HEADER' if chunk_text.startswith('#') else 'PARAGRAPH'
            chunks.append({
                'content': chunk_text,
                'type': chunk_type,
                'summary': chunk_text[:200] + '...' if len(chunk_text) > 200 else chunk_text
            })
            current_chunk = [line]
            current_size = line_size
        else:
            current_chunk.append(line)
            current_size += line_size
    
    # Add remaining chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk)
        chunk_type = 'HEADER' if chunk_text.startswith('#') else 'PARAGRAPH'
        chunks.append({
            'content': chunk_text,
            'type': chunk_type,
            'summary': chunk_text[:200] + '...' if len(chunk_text) > 200 else chunk_text
        })
    
    return chunks if chunks else [{
        'content': content,
        'type': 'PARAGRAPH',
        'summary': content[:200] + '...' if len(content) > 200 else content
    }]


# ============================================================================
# Main Seeding Logic
# ============================================================================

async def seed_github_repo(
    session: AsyncSession,
    owner: str,
    repo: str,
    branch: str = "main",
    github_token: Optional[str] = None
):
    """Seed database with GitHub repository data."""
    print(f"\n=== Seeding GitHub Repository: {owner}/{repo} (branch: {branch}) ===\n")
    
    # Initialize GitHub client
    client = GitHubClient(token=github_token)
    
    # 1. Bootstrap SysDict entries
    print("1. Bootstrapping SysDict...")
    sys_github = await get_or_create_sys_dict(session, "SOURCE", "GitHub")
    
    dtype_repo = await get_or_create_sys_dict(session, "DTYPE", "Repository")
    dtype_file = await get_or_create_sys_dict(session, "DTYPE", "File")
    dtype_dir = await get_or_create_sys_dict(session, "DTYPE", "Directory")
    
    pred_contains = await get_or_create_sys_dict(session, "PRED", "Contains")
    pred_depends_on = await get_or_create_sys_dict(session, "PRED", "Depends_On")
    pred_related_to = await get_or_create_sys_dict(session, "PRED", "Related_To")
    
    tag_python = await get_or_create_sys_dict(session, "TAG", "Python")
    tag_markdown = await get_or_create_sys_dict(session, "TAG", "Markdown")
    tag_config = await get_or_create_sys_dict(session, "TAG", "Config")
    
    editor_system = await get_or_create_sys_dict(session, "EDITOR", "System")
    
    await session.flush()
    print("  SysDict bootstrap complete.\n")
    
    # 2. Get repository info
    print("2. Fetching repository information...")
    repo_info = await client.get_repo_info(owner, repo)
    repo_description = repo_info.get("description", "")
    repo_language = repo_info.get("language", "")
    print(f"  Repository: {repo_info.get('full_name')}")
    print(f"  Description: {repo_description}")
    print(f"  Language: {repo_language}\n")
    
    # 3. Create repository OriginData
    print("3. Creating repository OriginData...")
    repo_urn = generate_urn("repository")
    stmt = select(OriginData).where(OriginData.urn == repo_urn)
    repo_data = (await session.execute(stmt)).scalar_one_or_none()
    
    if not repo_data:
        repo_data = OriginData(
            urn=repo_urn,
            src_sys_id=sys_github.id,
            dtype_id=dtype_repo.id,
            props={
                "name": repo,
                "owner": owner,
                "description": repo_description,
                "language": repo_language,
                "stars": repo_info.get("stargazers_count", 0),
                "forks": repo_info.get("forks_count", 0),
            }
        )
        session.add(repo_data)
        await session.flush()
        print(f"  Created Repository OriginData: {repo_urn} (id={repo_data.id})")
    else:
        print(f"  Repository already exists: {repo_urn} (id={repo_data.id})")
    
    # 4. Create root TreeNode
    print("\n4. Creating root TreeNode...")
    root_node = TreeNode(
        parent_id=None,
        data_id=repo_data.id,
        view_type="Folder",
        name=repo,
        slug=slugify(repo),
        ord=0
    )
    session.add(root_node)
    await session.flush()
    print(f"  Created root TreeNode: {root_node.name} (id={root_node.id})")
    
    # 5. Get file tree
    print("\n5. Fetching file tree...")
    file_tree = await client.get_file_tree(owner, repo, branch)
    files = [item for item in file_tree if item.get("type") == "blob"]
    dirs = [item for item in file_tree if item.get("type") == "tree"]
    print(f"  Found {len(files)} files and {len(dirs)} directories")
    
    # 6. Create directory structure in TreeNode
    print("\n6. Creating directory structure...")
    dir_map: Dict[str, TreeNode] = {}  # path -> TreeNode
    dir_map[""] = root_node  # root directory
    
    # Sort directories by depth (shallow first)
    sorted_dirs = sorted(dirs, key=lambda x: x["path"].count("/"))
    for dir_item in sorted_dirs:
        dir_path = dir_item["path"]
        parent_path, dir_name = os.path.split(dir_path) if dir_path else ("", "")
        parent_node = dir_map.get(parent_path, root_node)
        
        dir_node = TreeNode(
            parent_id=parent_node.id,
            data_id=None,  # Directory doesn't have OriginData
            view_type="Folder",
            name=dir_name or "root",
            slug=slugify(dir_name or "root"),
            ord=0
        )
        session.add(dir_node)
        await session.flush()
        dir_map[dir_path] = dir_node
        print(f"  Created directory: {dir_path}")
    
    # 7. Process files
    print(f"\n7. Processing {len(files)} files...")
    file_count = 0
    
    for file_item in files:
        file_path = file_item["path"]
        file_size = file_item.get("size", 0)
        
        # Skip large files (> 1MB)
        if file_size > 1024 * 1024:
            print(f"  Skipping large file: {file_path} ({file_size} bytes)")
            continue
        
        # Get file content
        content = await client.get_file_content(owner, repo, file_path, branch)
        if content is None:
            print(f"  Skipping (content not available): {file_path}")
            continue
        
        file_count += 1
        print(f"\n  Processing file {file_count}/{len(files)}: {file_path}")
        
        # Determine parent directory
        parent_path, filename = split_path(file_path)
        parent_node = dir_map.get(parent_path, root_node)
        
        # Determine file type and tags
        ext = os.path.splitext(filename)[1].lower()
        file_tags = []
        if ext in ['.py']:
            file_tags.append(tag_python.id)
        elif ext in ['.md', '.markdown']:
            file_tags.append(tag_markdown.id)
        elif ext in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']:
            file_tags.append(tag_config.id)
        
        # Create OriginData for file
        file_urn = generate_urn("file")
        file_data = OriginData(
            urn=file_urn,
            src_sys_id=sys_github.id,
            dtype_id=dtype_file.id,
            props={
                "path": file_path,
                "name": filename,
                "extension": ext.lstrip('.') if ext else None,
                "size": file_size,
            }
        )
        session.add(file_data)
        await session.flush()
        
        # Create TreeNode for file
        file_node = TreeNode(
            parent_id=parent_node.id,
            data_id=file_data.id,
            view_type="File",
            name=filename,
            slug=slugify(filename),
            ord=file_count
        )
        session.add(file_node)
        await session.flush()
        
        # Create BlobStore entry
        content_type = "text/plain"
        if ext in ['.md', '.markdown']:
            content_type = "text/markdown"
        elif ext in ['.py']:
            content_type = "text/x-python"
        elif ext in ['.json']:
            content_type = "application/json"
        
        blob_hash = await create_blob(session, content, content_type)
        
        # Create Revision
        title = f"Initial version of {filename}"
        revision = Revision(
            data_id=file_data.id,
            title=title,
            summary_hash=blob_hash,
            tags=file_tags if file_tags else None,
            editor_id=editor_system.id,
            meta_diff={
                "lines_added": len(content.splitlines()),
                "lines_removed": 0,
                "file_size": file_size
            }
        )
        session.add(revision)
        await session.flush()
        
        # Update OriginData with current revision
        file_data.curr_rev_id = revision.id
        
        # Create ChunkNodes for text files
        if content_type.startswith("text/"):
            chunks = split_into_chunks(content)
            for idx, chunk_data in enumerate(chunks):
                chunk_hash = hashlib.sha256(chunk_data['content'].encode('utf-8')).hexdigest()
                chunk_node = ChunkNode(
                    revision_id=revision.id,
                    chunk_hash=chunk_hash,
                    chunk_type=chunk_data['type'],
                    content_summary=chunk_data['summary'],
                    ord=idx
                )
                session.add(chunk_node)
        
        # Create KnowledgeEdge: Repository Contains File
        contains_edge = KnowledgeEdge(
            source_id=repo_data.id,
            target_id=file_data.id,
            predicate_id=pred_contains.id,
            weight=1.0
        )
        session.add(contains_edge)
        
        print(f"    Created OriginData: {file_urn} (id={file_data.id})")
        print(f"    Created TreeNode: {filename} (id={file_node.id})")
        print(f"    Created Revision: {title} (id={revision.id})")
    
    # 8. Commit all changes
    print("\n8. Committing changes to database...")
    await session.commit()
    print(f"\n=== Seeding complete! Processed {file_count} files ===\n")


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
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
    
    # Validate required arguments
    if not args.owner:
        print("Error: --owner is required. Set GITHUB_OWNER in .env file or provide --owner argument.", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    if not args.repo:
        print("Error: --repo is required. Set GITHUB_REPO in .env file or provide --repo argument.", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    try:
        async with AsyncSessionLocal() as session:
            await seed_github_repo(
                session,
                owner=args.owner,
                repo=args.repo,
                branch=args.branch,
                github_token=args.token
            )
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
