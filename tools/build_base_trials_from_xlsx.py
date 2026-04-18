"""
Export base trials per deck from the randomization Excel workbook.

Expected: 5 sheets named EAT_1..EAT_5 (or close).
Outputs: conditions/EAT_X/base_trials_EAT_X.csv
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
KEEP_COLS = ["deck","trial","arrow_direction","cue_color","cue_meaning","resolved_valence"]

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    rename_map = {
        "arrow": "arrow_direction",
        "arrowdir": "arrow_direction",
        "cue": "cue_color",
        "meaning": "cue_meaning",
        "valence": "resolved_valence",
    }
    for k,v in rename_map.items():
        if k in df.columns and v not in df.columns:
            df.rename(columns={k:v}, inplace=True)
    return df

def detect_deck_id(sheet_name: str) -> str:
    s = sheet_name.strip().upper()
    if s.startswith("EAT_") and s[4:].isdigit():
        return s
    m = re.search(r"(?:EAT)?\s*[_-]?\s*(\d)", s)
    return f"EAT_{m.group(1)}" if m else ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    args = ap.parse_args()

    xlsx = Path(args.xlsx)
    if not xlsx.exists():
        raise FileNotFoundError(xlsx)

    sheets = pd.read_excel(xlsx, sheet_name=None, engine="openpyxl")
    exported = 0
    for sheet_name, df in sheets.items():
        deck_id = detect_deck_id(sheet_name)
        if deck_id not in {f"EAT_{i}" for i in range(1,6)}:
            continue
        df = normalize_columns(df)
        missing = [c for c in KEEP_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"Sheet '{sheet_name}' missing columns {missing}. Found {list(df.columns)}")
        out = REPO_ROOT / "conditions" / deck_id / f"base_trials_{deck_id}.csv"
        # ensure the output directory exists
        out.parent.mkdir(parents=True, exist_ok=True)
        df[KEEP_COLS].to_csv(out, index=False)
        print(f"Exported {deck_id}: {len(df)} rows -> {out}")
        exported += 1

    if exported == 0:
        raise RuntimeError("No deck sheets found. Expected sheets named EAT_1..EAT_5 (or similar).")

if __name__ == "__main__":
    main()
