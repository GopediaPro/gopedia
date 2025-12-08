"""
GitHub API Client

External service client for interacting with GitHub API.
"""
from typing import Optional, Dict, List
import httpx
import base64


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
                    content = base64.b64decode(data.get("content", "")).decode("utf-8")
                    return content
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise
        return None
