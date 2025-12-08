"""
GitHub Seed Service

Service layer for seeding GitHub repository data into the database.
"""
import os
import hashlib
from typing import Optional, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.external.github_client import GitHubClient
from src.infrastructure.repositories.seed_repository import SeedRepository
from src.utils.helpers import generate_urn, slugify, split_path, split_into_chunks
from src.domain.entities import (
    OriginData, Revision, TreeNode, ChunkNode, KnowledgeEdge
)


class GitHubSeedService:
    """Service for seeding GitHub repository data."""
    
    def __init__(self, session: AsyncSession, github_client: GitHubClient):
        self.session = session
        self.github_client = github_client
        self.seed_repo = SeedRepository(session)
    
    async def seed_repository(
        self,
        owner: str,
        repo: str,
        branch: str = "main"
    ) -> int:
        """
        Seed database with GitHub repository data.
        
        Returns:
            Number of files processed
        """
        print(f"\n=== Seeding GitHub Repository: {owner}/{repo} (branch: {branch}) ===\n")
        
        # 1. Bootstrap SysDict entries
        print("1. Bootstrapping SysDict...")
        sys_github = await self.seed_repo.get_or_create_sys_dict("SOURCE", "GitHub")
        
        dtype_repo = await self.seed_repo.get_or_create_sys_dict("DTYPE", "Repository")
        dtype_file = await self.seed_repo.get_or_create_sys_dict("DTYPE", "File")
        dtype_dir = await self.seed_repo.get_or_create_sys_dict("DTYPE", "Directory")
        
        pred_contains = await self.seed_repo.get_or_create_sys_dict("PRED", "Contains")
        pred_depends_on = await self.seed_repo.get_or_create_sys_dict("PRED", "Depends_On")
        pred_related_to = await self.seed_repo.get_or_create_sys_dict("PRED", "Related_To")
        
        tag_python = await self.seed_repo.get_or_create_sys_dict("TAG", "Python")
        tag_markdown = await self.seed_repo.get_or_create_sys_dict("TAG", "Markdown")
        tag_config = await self.seed_repo.get_or_create_sys_dict("TAG", "Config")
        
        editor_system = await self.seed_repo.get_or_create_sys_dict("EDITOR", "System")
        
        await self.session.flush()
        print("  SysDict bootstrap complete.\n")
        
        # 2. Get repository info
        print("2. Fetching repository information...")
        repo_info = await self.github_client.get_repo_info(owner, repo)
        repo_description = repo_info.get("description", "")
        repo_language = repo_info.get("language", "")
        print(f"  Repository: {repo_info.get('full_name')}")
        print(f"  Description: {repo_description}")
        print(f"  Language: {repo_language}\n")
        
        # 3. Create repository OriginData
        repo_data = await self._create_repository_origin_data(
            repo, owner, repo_description, repo_language, repo_info,
            sys_github.id, dtype_repo.id
        )
        
        # 4. Create root TreeNode
        root_node = await self._create_root_tree_node(repo, repo_data.id)
        
        # 5. Get file tree
        print("\n5. Fetching file tree...")
        file_tree = await self.github_client.get_file_tree(owner, repo, branch)
        files = [item for item in file_tree if item.get("type") == "blob"]
        dirs = [item for item in file_tree if item.get("type") == "tree"]
        print(f"  Found {len(files)} files and {len(dirs)} directories")
        
        # 6. Create directory structure in TreeNode
        dir_map = await self._create_directory_structure(dirs, root_node)
        
        # 7. Process files
        file_count = await self._process_files(
            files, owner, repo, branch, dir_map, root_node,
            sys_github.id, dtype_file.id, repo_data.id,
            tag_python.id, tag_markdown.id, tag_config.id,
            pred_contains.id, editor_system.id
        )
        
        # 8. Commit all changes
        print("\n8. Committing changes to database...")
        await self.session.commit()
        print(f"\n=== Seeding complete! Processed {file_count} files ===\n")
        
        return file_count
    
    async def _create_repository_origin_data(
        self,
        repo: str,
        owner: str,
        description: str,
        language: str,
        repo_info: Dict,
        sys_github_id: int,
        dtype_repo_id: int
    ) -> OriginData:
        """Create repository OriginData."""
        print("3. Creating repository OriginData...")
        repo_urn = generate_urn("repository")
        stmt = select(OriginData).where(OriginData.urn == repo_urn)
        repo_data = (await self.session.execute(stmt)).scalar_one_or_none()
        
        if not repo_data:
            repo_data = OriginData(
                urn=repo_urn,
                src_sys_id=sys_github_id,
                dtype_id=dtype_repo_id,
                props={
                    "name": repo,
                    "owner": owner,
                    "description": description,
                    "language": language,
                    "stars": repo_info.get("stargazers_count", 0),
                    "forks": repo_info.get("forks_count", 0),
                }
            )
            self.session.add(repo_data)
            await self.session.flush()
            print(f"  Created Repository OriginData: {repo_urn} (id={repo_data.id})")
        else:
            print(f"  Repository already exists: {repo_urn} (id={repo_data.id})")
        
        return repo_data
    
    async def _create_root_tree_node(self, repo: str, repo_data_id: int) -> TreeNode:
        """Create root TreeNode."""
        print("\n4. Creating root TreeNode...")
        root_node = TreeNode(
            parent_id=None,
            data_id=repo_data_id,
            view_type="Folder",
            name=repo,
            slug=slugify(repo),
            ord=0
        )
        self.session.add(root_node)
        await self.session.flush()
        print(f"  Created root TreeNode: {root_node.name} (id={root_node.id})")
        return root_node
    
    async def _create_directory_structure(
        self,
        dirs: list[Dict],
        root_node: TreeNode
    ) -> Dict[str, TreeNode]:
        """Create directory structure in TreeNode. Returns dir_map."""
        print("\n6. Creating directory structure...")
        dir_map: Dict[str, TreeNode] = {}
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
            self.session.add(dir_node)
            await self.session.flush()
            dir_map[dir_path] = dir_node
            print(f"  Created directory: {dir_path}")
        
        return dir_map
    
    async def _process_files(
        self,
        files: list[Dict],
        owner: str,
        repo: str,
        branch: str,
        dir_map: Dict[str, TreeNode],
        root_node: TreeNode,
        sys_github_id: int,
        dtype_file_id: int,
        repo_data_id: int,
        tag_python_id: int,
        tag_markdown_id: int,
        tag_config_id: int,
        pred_contains_id: int,
        editor_system_id: int
    ) -> int:
        """Process files and create database entries. Returns file count."""
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
            content = await self.github_client.get_file_content(owner, repo, file_path, branch)
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
                file_tags.append(tag_python_id)
            elif ext in ['.md', '.markdown']:
                file_tags.append(tag_markdown_id)
            elif ext in ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg']:
                file_tags.append(tag_config_id)
            
            # Create OriginData for file
            file_urn = generate_urn("file")
            file_data = OriginData(
                urn=file_urn,
                src_sys_id=sys_github_id,
                dtype_id=dtype_file_id,
                props={
                    "path": file_path,
                    "name": filename,
                    "extension": ext.lstrip('.') if ext else None,
                    "size": file_size,
                }
            )
            self.session.add(file_data)
            await self.session.flush()
            
            # Create TreeNode for file
            file_node = TreeNode(
                parent_id=parent_node.id,
                data_id=file_data.id,
                view_type="File",
                name=filename,
                slug=slugify(filename),
                ord=file_count
            )
            self.session.add(file_node)
            await self.session.flush()
            
            # Create BlobStore entry
            content_type = self._get_content_type(ext)
            blob_hash = await self.seed_repo.create_or_get_blob(content, content_type)
            
            # Create Revision
            title = f"Initial version of {filename}"
            revision = Revision(
                data_id=file_data.id,
                title=title,
                summary_hash=blob_hash,
                tags=file_tags if file_tags else None,
                editor_id=editor_system_id,
                meta_diff={
                    "lines_added": len(content.splitlines()),
                    "lines_removed": 0,
                    "file_size": file_size
                }
            )
            self.session.add(revision)
            await self.session.flush()
            
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
                    self.session.add(chunk_node)
            
            # Create KnowledgeEdge: Repository Contains File
            contains_edge = KnowledgeEdge(
                source_id=repo_data_id,
                target_id=file_data.id,
                predicate_id=pred_contains_id,
                weight=1.0
            )
            self.session.add(contains_edge)
            
            print(f"    Created OriginData: {file_urn} (id={file_data.id})")
            print(f"    Created TreeNode: {filename} (id={file_node.id})")
            print(f"    Created Revision: {title} (id={revision.id})")
        
        return file_count
    
    def _get_content_type(self, ext: str) -> str:
        """Get content type based on file extension."""
        if ext in ['.md', '.markdown']:
            return "text/markdown"
        elif ext in ['.py']:
            return "text/x-python"
        elif ext in ['.json']:
            return "application/json"
        else:
            return "text/plain"
