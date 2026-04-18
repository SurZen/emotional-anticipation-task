"""
Verify generated deck trial files for balance, duplicates, blanks.
Usage: python tools/verify_decks.py
"""
from pathlib import Path
import csv
from collections import Counter, defaultdict

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT = REPO_ROOT / "conditions"

all_used = []
summary = []
for i in range(1,6):
    deck = f"EAT_{i}"
    path = OUT / deck / f"trials_{deck}.csv"
    if not path.exists():
        print(f"Missing {path}")
        continue
    total = 0
    resolved = Counter()
    image_blanks = 0
    dup_checker = Counter()
    per_cat = Counter()
    with path.open(newline='', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            total += 1
            rv = row.get('resolved_valence','').strip().lower()
            resolved[rv] += 1
            img = row.get('relative_path') or row.get('image_path') or ''
            # image_path may be full path 'stimuli/pools/...' -- try to extract relative part
            if img and img.startswith('stimuli/pools/'):
                rel = img[len('stimuli/pools/'):]
            else:
                rel = img
            if not rel or rel.strip() == '' or rel.strip() == 'stimuli/pools/':
                image_blanks += 1
            else:
                dup_checker[rel] += 1
                all_used.append(rel)
            cat = row.get('image_category') or ''
            if cat:
                per_cat[cat] += 1
    duplicates = [k for k,v in dup_checker.items() if v>1]
    summary.append((deck, total, dict(resolved), image_blanks, len(duplicates), dict(per_cat)))

# cross-deck duplicates
cross_dups = [k for k,v in Counter(all_used).items() if v>1]

print('Per-deck summary:')
for s in summary:
    deck,total,resolved,blanks,dups,per_cat = s
    print(f"{deck}: total={total}, resolved={resolved}, blanks={blanks}, duplicate_image_paths={dups}")
    if per_cat:
        print('  per_category_counts:', per_cat)

print(f"Cross-deck repeated images: {len(cross_dups)}")
if cross_dups:
    print('Some repeated image paths across decks (first 20):')
    print('\n'.join(cross_dups[:20]))

print('Done')
