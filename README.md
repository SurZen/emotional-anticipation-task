# MaM EAT (PsychoPy) — Project Skeleton + Deck Builder Tools

This is a **contained project skeleton** for building a 5-deck Emotional Anticipation Task (EAT) in PsychoPy.

## What you do
1) **Unzip** this folder on the target laptop.
2) Copy your image folders into `stimuli/pools/...` (folders already created).
3) Copy your randomization workbook into `manifests/` (or point the script to it).
4) Run the build scripts to generate the final per-deck conditions files.

## Folder highlights
- `stimuli/pools/` — master image pools (YOU copy images here)
- `conditions/EAT_X/` — per-deck conditions files (generated)
- `tools/` — build scripts
- `experiment/` — PsychoPy Builder project (placeholder included)

## Quickstart (after images + workbook are in place)
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

python tools/generate_image_catalog.py
python tools/build_base_trials_from_xlsx.py --xlsx manifests/MaM_EAT_randomized_stimuli.xlsx
python tools/assign_images_and_jitters.py
python tools/validate_decks.py
```

### PsychoPy deck selection
In Builder, add a startup dialog field called `deck_id` with choices:
`EAT_1,EAT_2,EAT_3,EAT_4,EAT_5`

Then in **Begin Experiment** code:
```python
from experiment.code.deck_router import resolve_conditions_file
deck_id = expInfo.get('deck_id', 'EAT_1')
conditions_file = resolve_conditions_file(deck_id)
```

Finally set your main loop's `conditions` to: `$conditions_file`
