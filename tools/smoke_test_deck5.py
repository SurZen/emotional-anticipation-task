from pathlib import Path
import csv

REPO = Path(__file__).resolve().parents[1]
DECK = 'EAT_5'
CSV = REPO / 'conditions' / DECK / f'trials_{DECK}.csv'

if not CSV.exists():
    print('Deck CSV not found:', CSV)
    raise SystemExit(1)

missing = []
not_readable = []
count = 0

with CSV.open(encoding='utf-8', newline='') as f:
    r = csv.DictReader(f)
    for row in r:
        count += 1
        img = (row.get('image_path') or '').strip()
        if not img:
            missing.append((row.get('trial',''), img))
            continue
        p = REPO / img
        if not p.exists():
            missing.append((row.get('trial',''), str(p)))

print('Checked', count, 'rows in', CSV)
if not missing:
    print('All image paths exist on disk.')
else:
    print('Missing/unresolved images:', len(missing))
    for t, p in missing:
        print(' trial', t, '->', p)

# exit code 0 if all present, 2 if any missing
raise SystemExit(0 if not missing else 2)
