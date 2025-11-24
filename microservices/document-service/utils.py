import os
import hashlib
import uuid
from typing import List


def get_file_size(filepath: str) -> int:
    """Get the size of a file in bytes."""
    return os.path.getsize(filepath)


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename by adding a UUID prefix."""
    name, ext = os.path.splitext(original_filename)
    unique_name = f"{uuid.uuid4().hex[:8]}_{name}{ext}"
    return unique_name


def ensure_directory_exists(path: str):
    """Ensure directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)


def calculate_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def validate_file_type(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate if file extension is in allowed list."""
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_extensions