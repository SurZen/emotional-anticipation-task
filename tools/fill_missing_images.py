"""Fill blank image trials in a deck using unused images from manifests/image_catalog.csv
Usage: python tools/fill_missing_images.py --deck EAT_5
This script backs up the deck CSV and deck_assignments.csv before modifying.
"""
from pathlib import Path
import csv
import argparse
import random

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG = REPO_ROOT / "manifests" / "image_catalog.csv"
ASSIGN = REPO_ROOT / "manifests" / "deck_assignments.csv"

POS_CATS = ["Cute_Animals","Food_Drinks","Landscapes_Nature","Objects_Positive","People_Children","Positive_People","Recreation_Sports"]
NEG_CATS = ["Dead_Animals","Dead_People","Injury_Wounds_Blood","Negative_Circumstances","Negative_Objects","Sad_Negative_Facial_Expressions","Threatening_Animals","Violence_Weapons"]

def load_catalog():
    rows = []
    with CATALOG.open(encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append({
                'relative_path': row['relative_path'],
                'valence': row['valence'],
                'category': row['category'],
                'filename': row['filename']
            })
    return rows

def load_assignments():
    used = set()
    if not ASSIGN.exists():
        return used, []
    with ASSIGN.open(encoding='utf-8') as f:
        r = csv.DictReader(f)
        rows = list(r)
    for row in rows:
        rel = (row.get('relative_path') or '').strip()
        if rel:
            used.add(rel)
    return used, rows

def backup(path: Path):
    if path.exists():
        path.with_suffix(path.suffix + '.bak').write_bytes(path.read_bytes())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--deck', required=True)
    ap.add_argument('--seed', type=int, default=20251229)
    args = ap.parse_args()

    deck = args.deck
    deck_csv = REPO_ROOT / 'conditions' / deck / f'trials_{deck}.csv'
    if not deck_csv.exists():
        raise FileNotFoundError(deck_csv)

    catalog = load_catalog()
    used, assign_rows = load_assignments()

    # build available per valence
    avail = {'positive': [], 'negative': []}
    for r in catalog:
        if r['relative_path'] not in used:
            avail[r['valence']].append(r)

    random.seed(args.seed)

    # read deck rows
    with deck_csv.open(encoding='utf-8', newline='') as f:
        r = csv.DictReader(f)
        deck_rows = list(r)
        fieldnames = r.fieldnames

    blanks = []
    for i, row in enumerate(deck_rows):
        img_path = (row.get('image_path') or '').strip()
        if not img_path or img_path.strip() == 'stimuli/pools/':
            blanks.append(i)

    if not blanks:
        print('No blank image trials found in', deck)
        return

    print(f'Found {len(blanks)} blank trials in {deck}: indices/trials {[ (i+1, deck_rows[i].get("trial")) for i in blanks ]}')

    used_local = set(used)  # to track newly used
    fills = []
    for idx in blanks:
        row = deck_rows[idx]
        rv = (row.get('resolved_valence') or '').strip().lower()
        if rv not in ('positive','negative'):
            print(f"Skipping trial {row.get('trial')} with unresolved valence: {rv}")
            continue
        choices = avail.get(rv, [])
        # remove any that may have been used in this filling
        choices = [c for c in choices if c['relative_path'] not in used_local]
        if not choices:
            print(f"No available {rv} images left to fill trial {row.get('trial')}")
            continue
        pick = random.choice(choices)
        used_local.add(pick['relative_path'])
        fills.append((idx, pick))

    if not fills:
        print('No fills performed (no available images).')
        return

    # backup files
    backup(deck_csv)
    if ASSIGN.exists():
        backup(ASSIGN)

    # apply fills to deck_rows
    for idx, pick in fills:
        row = deck_rows[idx]
        row['image_path'] = 'stimuli/pools/' + pick['relative_path']
        row['image_category'] = pick['category']
        row['image_valence'] = pick['valence']
        # event_code_image left as-is; caller can re-run assign_images script if needed

    # write updated deck CSV
    with deck_csv.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(deck_rows)

    # update deck_assignments.csv by appending new filled rows
    new_assigns = []
    for idx, pick in fills:
        row = deck_rows[idx]
        new_assigns.append({
            'deck': deck,
            'trial': row.get('trial',''),
            'resolved_valence': row.get('resolved_valence',''),
            'category': pick['category'],
            'relative_path': pick['relative_path']
        })

    # append to assignments
    if ASSIGN.exists():
        with ASSIGN.open('a', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['deck','trial','resolved_valence','category','relative_path'])
            for a in new_assigns:
                w.writerow(a)
    else:
        with ASSIGN.open('w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=['deck','trial','resolved_valence','category','relative_path'])
            w.writeheader(); w.writerows(new_assigns)

    print(f'Filled {len(fills)} trials in {deck}:')
    for idx, pick in fills:
        print(f" trial {deck_rows[idx].get('trial')}: {pick['relative_path']} ({pick['category']}, {pick['valence']})")

if __name__ == '__main__':
    main()
