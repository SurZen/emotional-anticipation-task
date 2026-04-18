"""
Validate no duplicate images across decks and append summary stats to manifests/qc_report.txt
"""
from __future__ import annotations
from pathlib import Path
from collections import Counter
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]

def main():
    assign_path = REPO_ROOT/"manifests/deck_assignments.csv"
    if not assign_path.exists():
        raise FileNotFoundError("Run tools/assign_images_and_jitters.py first (deck_assignments.csv missing).")
    df = pd.read_csv(assign_path)
    dup = [k for k,v in Counter(df["relative_path"].tolist()).items() if v > 1]
    if dup:
        raise RuntimeError(f"Duplicate images across decks: {dup[:10]} ...")

    out_lines = []
    for deck in sorted(df["deck"].unique()):
        sub = df[df["deck"]==deck]
        out_lines.append(f"== {deck} SUMMARY ==")
        out_lines.append(f"Trials: {len(sub)}")
        out_lines.append("Valence: " + str(sub["resolved_valence"].value_counts().to_dict()))
        out_lines.append("Category: " + str(sub["category"].value_counts().to_dict()))
        out_lines.append("")
    report = REPO_ROOT/"manifests/qc_report.txt"
    existing = report.read_text(encoding="utf-8") if report.exists() else ""
    report.write_text(existing + "\n\n" + "\n".join(out_lines), encoding="utf-8")
    print("Validation passed (no duplicates). Updated manifests/qc_report.txt")

if __name__ == "__main__":
    main()
