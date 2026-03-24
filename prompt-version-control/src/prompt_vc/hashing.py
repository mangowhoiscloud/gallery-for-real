"""SHA256 hashing utilities for prompt-version-control."""

import hashlib
from pathlib import Path


def hash_file(path: Path) -> str:
    """Return the SHA256 hex digest of the file at `path`."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def hash_version(files: dict[str, str]) -> str:
    """Return a deterministic SHA256 digest for a set of filename->hash pairs.

    Order-independent: sorts by filename before hashing so the same logical
    snapshot always produces the same version hash regardless of insertion order.
    """
    h = hashlib.sha256()
    for filename in sorted(files):
        h.update(f"{filename}:{files[filename]}\n".encode())
    return h.hexdigest()
