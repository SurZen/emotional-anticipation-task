from __future__ import annotations
from pathlib import Path

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}

def iter_images(root: Path):
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS:
            yield p

def norm_relpath(path: Path, base: Path) -> str:
    return str(path.relative_to(base)).replace("\\", "/")
