"""
Scan stimuli/pools and create manifests/image_catalog.csv
"""
from __future__ import annotations
import csv
from pathlib import Path
import sys

# Ensure repository root is on sys.path so `from experiment.code...` works
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiment.code.utils import iter_images, norm_relpath

POOLS_ROOT = REPO_ROOT / "stimuli" / "pools"
OUTFILE = REPO_ROOT / "manifests" / "image_catalog.csv"

import re

def normalize_category_name(name: str) -> str:
    if not name:
        return ""
    # remove parenthetical content, collapse whitespace, replace spaces with underscores
    out = re.sub(r"\s*\(.*?\)\s*", "", name).strip()
    out = "_".join(out.split())
    return out

def infer_valence(relpath: str) -> str:
    # Normalize and ignore __MACOSX artifacts
    parts = [p for p in relpath.split("/") if p and p != "__MACOSX"]
    # Look for an explicit Organized folder name in any path component
    for p in parts:
        pl = p.lower()
        if "positive" in pl and "organ" in pl:
            return "positive"
        if "negative" in pl and "organ" in pl:
            return "negative"

    # Fallback: if the first component contains positive/negative
    if parts:
        first = parts[0].lower()
        if "positive" in first:
            return "positive"
        if "negative" in first:
            return "negative"

    raise ValueError(f"Could not infer valence from path: {relpath}")

def infer_category_subcategory(relpath: str):
    parts = [p for p in relpath.split("/") if p and p != "__MACOSX"]
    category = ""
    subcat = ""

    if not parts:
        return (category, subcat)

    first = parts[0].lower()
    is_top_organized = ("organ" in first) and ("positive" in first or "negative" in first)

    if is_top_organized:
        # find the next meaningful part that's not another Organized wrapper
        idx = 1
        while idx < len(parts) and ("organ" in parts[idx].lower() and ("positive" in parts[idx].lower() or "negative" in parts[idx].lower())):
            idx += 1
        if idx < len(parts):
            category = parts[idx]
            # subcategory for certain multi-level categories
            if idx + 1 < len(parts):
                cat_low = category.lower()
                if cat_low.startswith("threatening") or cat_low.startswith("objects"):
                    subcat = parts[idx + 1]
        else:
            category = parts[0]
    else:
        category = parts[0]
        if len(parts) >= 2:
            cat_low = category.lower()
            if cat_low.startswith("threatening") or cat_low.startswith("objects"):
                subcat = parts[1]

    return (category, subcat)

def main():
    rows = []
    for img in iter_images(POOLS_ROOT):
        rel = norm_relpath(img, POOLS_ROOT)
        # skip macOS __MACOSX metadata folders and resource-fork files
        if "__MACOSX" in rel or img.name.startswith("._") or img.name == ".DS_Store":
            continue
        valence = infer_valence(rel)
        category, subcat = infer_category_subcategory(rel)
        # normalize category/subcategory names to underscore-style keys
        category = normalize_category_name(category)
        subcat = normalize_category_name(subcat)
        rows.append({
            "filename": img.name,
            "relative_path": rel,
            "valence": valence,
            "category": category,
            "subcategory": subcat
        })

    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    with OUTFILE.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["filename","relative_path","valence","category","subcategory"])
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["valence"], r["category"], r["subcategory"], r["filename"])))

    print(f"Wrote {len(rows)} rows -> {OUTFILE}")

if __name__ == "__main__":
    main()
