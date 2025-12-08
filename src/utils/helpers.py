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


def split_into_chunks(content: str, max_chunk_size: int = 1000) -> list[dict[str, str]]:
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
