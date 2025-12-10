"""
Utility Helper Functions

Common utility functions used across the application.
"""
import os
import re
from typing import Optional, Tuple
from uuid import uuid4


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
