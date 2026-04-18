"""Merge trial-level assignments from a conditions deck into manifests/deck_assignments.csv
Usage: python tools/merge_deck_from_conditions.py --deck EAT_5
This will back up `manifests/deck_assignments.csv` to `.bak` and replace any existing rows for the deck
with rows derived from the deck CSV's `image_path`, `image_category`, and `resolved_valence` fields.
"""
from pathlib import Path
import csv
import argparse

REPO = Path(__file__).resolve().parents[1]
MANIFEST = REPO / 'manifests' / 'deck_assignments.csv'


def load_existing():
    if not MANIFEST.exists():
        return [], ['deck','trial','resolved_valence','category','relative_path']
    with MANIFEST.open(encoding='utf-8', newline='') as f:
        r = csv.DictReader(f)
        return list(r), r.fieldnames


def backup(path: Path):
    if path.exists():
        path.with_suffix(path.suffix + '.bak').write_bytes(path.read_bytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--deck', required=False, help='Deck id to merge, e.g. EAT_5')
    ap.add_argument('--all', action='store_true', help='Merge all decks found under conditions/')
    args = ap.parse_args()

    decks_to_process = []
    if args.all:
        # detect all decks in conditions directory starting with EAT_
        for p in (REPO / 'conditions').iterdir():
            if p.is_dir() and p.name.startswith('EAT_'):
                decks_to_process.append(p.name)
    elif args.deck:
        decks_to_process = [args.deck]
    else:
        raise SystemExit('Specify --deck DECK or --all')

    all_new_assigns = []
    for deck in decks_to_process:
        deck_csv = REPO / 'conditions' / deck / f'trials_{deck}.csv'
        if not deck_csv.exists():
            print(f'Warning: deck CSV not found, skipping: {deck_csv}')
            continue
        with deck_csv.open(encoding='utf-8', newline='') as f:
            rdr = csv.DictReader(f)
            deck_rows = list(rdr)

        for row in deck_rows:
            rel = (row.get('image_path') or '').strip()
            if rel.startswith('stimuli/pools/'):
                rel2 = rel[len('stimuli/pools/'):]
            else:
                rel2 = rel
            all_new_assigns.append({
                'deck': deck,
                'trial': row.get('trial',''),
                'resolved_valence': row.get('resolved_valence',''),
                'category': row.get('image_category',''),
                'relative_path': rel2
            })

    exists_rows, fieldnames = load_existing()
    # filter out any existing rows for the decks we're replacing
    decks_set = set([r for r in decks_to_process])
    filtered = [r for r in exists_rows if (r.get('deck') or '') not in decks_set]

    out_rows = filtered + all_new_assigns

    backup(MANIFEST)
    with MANIFEST.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['deck','trial','resolved_valence','category','relative_path'])
        w.writeheader()
        w.writerows(out_rows)

    print(f'Replaced {len(decks_to_process)} deck(s) in {MANIFEST} (backup at {MANIFEST}.bak)')


if __name__ == '__main__':
    main()
