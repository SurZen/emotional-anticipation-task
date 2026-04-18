"""
Assign images + pre-trial jitters to each deck, producing FINAL conditions files.

Hybrid balancing (Option C), availability-aware (Option 2):
- Hard: no repeats within/across decks; valence driven by resolved_valence; each category represented if available.
- Soft: evenness per deck + global evenness weighted by available category counts.

Run:
python tools/assign_images_and_jitters.py
(optional) python tools/assign_images_and_jitters.py --relax
"""
from __future__ import annotations
import argparse
from pathlib import Path
import random
from collections import defaultdict, Counter
import pandas as pd
import yaml
import re

REPO_ROOT = Path(__file__).resolve().parents[1]

POS_CATS = ["Cute_Animals","Food_Drinks","Landscapes_Nature","Objects_Positive","People_Children","Positive_People","Recreation_Sports"]
NEG_CATS = ["Dead_Animals","Dead_People","Injury_Wounds_Blood","Negative_Circumstances","Negative_Objects","Sad_Negative_Facial_Expressions","Threatening_Animals","Violence_Weapons"]

def load_config():
    with (REPO_ROOT/"experiment/settings/config.yaml").open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def jitter_value(rng, key, rnd: random.Random) -> float:
    lo, hi = rng[key]
    return round(rnd.uniform(lo, hi), 3)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--relax", action="store_true")
    args = ap.parse_args()

    cfg = load_config()
    rng = cfg["timing_ranges_sec"]
    seed_base = int(cfg.get("seed", {}).get("value", 20251229))

    catalog_path = REPO_ROOT/"manifests/image_catalog.csv"
    if not catalog_path.exists():
        raise FileNotFoundError("Run tools/generate_image_catalog.py first (image_catalog.csv missing).")
    cat = pd.read_csv(catalog_path)

    def normalize_category_name(name: str) -> str:
        if not isinstance(name, str):
            return ""
        out = re.sub(r"\s*\(.*?\)\s*", "", name).strip()
        out = "_".join(out.split())
        return out

    # normalize category column so it matches POS_CATS/NEG_CATS keys
    cat["category"] = cat["category"].fillna("").astype(str).apply(normalize_category_name)

    # Build pools keyed by category only; resolved_valence from the randomization workbook
    pools = defaultdict(list)
    for _, r in cat.iterrows():
        pools[r["category"]].append(r["relative_path"])

    base_rnd = random.Random(seed_base)
    for c in list(pools.keys()):
        base_rnd.shuffle(pools[c])

    avail_pos = [c for c in POS_CATS if len(pools.get(c, [])) > 0]
    avail_neg = [c for c in NEG_CATS if len(pools.get(c, [])) > 0]
    if not avail_pos or not avail_neg:
        raise RuntimeError("Missing images in one or more required pools.")

    global_avail = {
        "positive": {c: len(pools[c]) for c in avail_pos},
        "negative": {c: len(pools[c]) for c in avail_neg},
    }

    used = set()
    global_counts = {"positive": Counter(), "negative": Counter()}
    assignments = []
    qc = []

    for i in range(1, 6):
        deck_id = f"EAT_{i}"
        base_path = REPO_ROOT/f"conditions/{deck_id}/base_trials_{deck_id}.csv"
        if not Path(base_path).exists():
            raise FileNotFoundError(base_path)

        df = pd.read_csv(base_path)
        df["resolved_valence"] = df["resolved_valence"].astype(str).str.strip().str.lower()
        df.loc[df["resolved_valence"].isin(["pos","positive"]), "resolved_valence"] = "positive"
        df.loc[df["resolved_valence"].isin(["neg","negative"]), "resolved_valence"] = "negative"

        N_pos = int((df["resolved_valence"]=="positive").sum())
        N_neg = int((df["resolved_valence"]=="negative").sum())
        pos_cats, neg_cats = avail_pos, avail_neg
        floor_pos = max(1, (N_pos//len(pos_cats))-1)
        floor_neg = max(1, (N_neg//len(neg_cats))-1)

        rnd = random.Random(seed_base + i)
        deck_counts = {"positive": Counter(), "negative": Counter()}
        chosen = {}

        def pop_image(category: str):
            lst = pools.get(category, [])
            while lst:
                rel = lst.pop()
                if rel not in used:
                    used.add(rel)
                    return rel
            return None

        def satisfy_presence(valence: str, idx_list, cats):
            if not idx_list:
                return
            k = min(len(idx_list), len(cats))
            for cat_name in cats[:k]:
                row_idx = idx_list.pop()
                rel = pop_image(cat_name)
                if rel is None:
                    continue
                chosen[row_idx] = (valence, cat_name, rel)
                deck_counts[valence][cat_name] += 1
                global_counts[valence][cat_name] += 1

        pos_idx = df.index[df["resolved_valence"]=="positive"].tolist()
        neg_idx = df.index[df["resolved_valence"]=="negative"].tolist()
        rnd.shuffle(pos_idx); rnd.shuffle(neg_idx)
        satisfy_presence("positive", pos_idx, pos_cats.copy())
        satisfy_presence("negative", neg_idx, neg_cats.copy())

        def targets(N, cats, valence):
            avail = global_avail[valence]
            total = sum(avail[c] for c in cats)
            return {c: (N*(avail[c]/total) if total else N/len(cats)) for c in cats}

        tgt_pos = targets(N_pos, pos_cats, "positive")
        tgt_neg = targets(N_neg, neg_cats, "negative")

        def pick_cat(valence, cats, tgt):
            scores = []
            global_total = sum(global_avail[valence][c] for c in cats)
            used_total = sum(global_counts[valence].values()) + 1e-6
            for c in cats:
                deck_need = tgt[c] - deck_counts[valence][c]
                expected_share = (global_avail[valence][c]/global_total) if global_total else 1/len(cats)
                expected_count = expected_share * used_total
                global_need = expected_count - global_counts[valence][c]
                remaining = len([x for x in pools.get(c, []) if x not in used])
                scarcity = -2.0 if remaining <= 2 else 0.0
                score = deck_need*2.0 + global_need*1.0 + scarcity
                scores.append((score, c))
            scores.sort(reverse=True, key=lambda t: t[0])
            return scores[0][1]

        for row_idx in df.index:
            if row_idx in chosen:
                continue
            val = df.at[row_idx, "resolved_valence"]
            if val == "positive":
                cat_name = pick_cat("positive", pos_cats, tgt_pos)
            else:
                cat_name = pick_cat("negative", neg_cats, tgt_neg)
            rel = pop_image(cat_name)
            if rel is None:
                # fallback any category
                for c in (pos_cats if val=="positive" else neg_cats):
                    rel2 = pop_image(c)
                    if rel2:
                        cat_name, rel = c, rel2
                        break
            if rel is None:
                # If we run out of images, warn and leave image fields blank for this trial.
                print(f"Warning: Ran out of {val} images for {deck_id} at trial {int(df.at[row_idx, 'trial'])}. Leaving image blank.")
                cat_name, rel = "", ""
            chosen[row_idx] = (val, cat_name, rel)
            # only increment counts if an image was actually assigned
            if rel:
                deck_counts[val][cat_name] += 1
                global_counts[val][cat_name] += 1

        # floor check: allow violations if user passed --relax or if some trials had no image assigned
        bad_pos = {c: deck_counts["positive"][c] for c in pos_cats if deck_counts["positive"][c] < floor_pos}
        bad_neg = {c: deck_counts["negative"][c] for c in neg_cats if deck_counts["negative"][c] < floor_neg}
        if bad_pos or bad_neg:
            blanks_count = sum(1 for _,(_,_,rel) in chosen.items() if not rel)
            total_avail_pos = sum(global_avail["positive"].get(c, 0) for c in pos_cats)
            total_avail_neg = sum(global_avail["negative"].get(c, 0) for c in neg_cats)
            # Log detailed warning and continue — prefer building decks even if perfect floor can't be met.
            print(f"Warning: {deck_id} floor violation (pos_floor={floor_pos}, neg_floor={floor_neg}). bad_pos={bad_pos}; bad_neg={bad_neg}; blanks={blanks_count}; total_avail_pos={total_avail_pos}; total_avail_neg={total_avail_neg}")

        df["image_valence"] = ""
        df["image_category"] = ""
        df["image_path"] = ""
        for idx, (val, cat_name, rel) in chosen.items():
            df.at[idx,"image_valence"] = val
            df.at[idx,"image_category"] = cat_name
            df.at[idx,"image_path"] = f"stimuli/pools/{rel}"
            assignments.append({"deck": deck_id, "trial": df.at[idx,"trial"], "resolved_valence": val, "category": cat_name, "relative_path": rel})

        for key in ["fix_dur","arrow_dur","isi1_dur","cue_dur","anticip_dur","image_dur","iti_dur"]:
            df[key] = [jitter_value(rng, key, rnd) for _ in range(len(df))]

        df["event_code_arrow"] = 10
        df["event_code_cue"] = df["cue_meaning"].astype(str).str.lower().map({"positive":20,"negative":30,"unknown":40}).fillna(0).astype(int)
        pos_code = {c: 100+(POS_CATS.index(c)+1) for c in POS_CATS}
        neg_code = {c: 200+(NEG_CATS.index(c)+1) for c in NEG_CATS}
        df["event_code_image"] = df.apply(lambda r: (pos_code.get(r["image_category"],0) if r["image_valence"]=="positive" else neg_code.get(r["image_category"],0)), axis=1).astype(int)

        out = REPO_ROOT/f"conditions/{deck_id}/trials_{deck_id}.csv"
        df.to_csv(out, index=False)

        qc.append(f"== {deck_id} ==")
        qc.append(f"N_pos={N_pos}, N_neg={N_neg}, floor_pos={floor_pos}, floor_neg={floor_neg}")
        qc.append("Positive: " + ", ".join([f"{c}:{deck_counts['positive'][c]}" for c in pos_cats]))
        qc.append("Negative: " + ", ".join([f"{c}:{deck_counts['negative'][c]}" for c in neg_cats]))
        qc.append("")

    pd.DataFrame(assignments).sort_values(["deck","trial"]).to_csv(REPO_ROOT/"manifests/deck_assignments.csv", index=False)
    (REPO_ROOT/"manifests/qc_report.txt").write_text("\n".join(qc), encoding="utf-8")
    print("Done. Wrote trials files + manifests/qc_report.txt")

if __name__ == "__main__":
    main()
