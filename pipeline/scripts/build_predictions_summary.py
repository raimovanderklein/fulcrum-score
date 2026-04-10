"""build_predictions_summary.py — Export the numeric facts from encounter.db
to a compact JSON file that the website can read alongside its hand-curated
reports.json.

The website's reports.json contains editorial prose (deck copy, headlines,
result narratives). It is hand-edited and not auto-generated.

This script produces predictions_summary.json — the *numeric ground truth*
for each trial: predicted value, direction, confidence, layer ORRs, falsifier,
method, prediction date, plus any matching readout and score.

The website templates can read this file to display the "current framework
prediction" section without forcing the prose into a database. The reports.json
slug maps to the trial_id here.

Output: pipeline/data/predictions_summary.json
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone

_HERE = Path(__file__).parent
_DATA = _HERE.parent / "data"

DB = _DATA / "encounter.db"
OUT = _DATA / "predictions_summary.json"


# Map encounter trial_id → website report slug (where they differ)
TRIAL_TO_SLUG = {
    "volga": "volga-bladder-periop",
    "energize": "energize-bladder-periop",
    "imbrave251": "imbrave251-hcc-2l",
    "keylynk_012": "keylynk-012-nsclc-3",
    "harmony_melanoma": "harmony-melanoma-fianlimab",
    "star_221": "star-221-tigit-gastric",
    "dellphi_312": "dellphi-312-sclc-1l",
    "keyvibe_006": "keyvibe-006-tigit-nsclc",
    "latify": "latify-atr-nsclc",
    "tinivo_2": "tinivo-2-rcc-2l",
}


def main():
    if not DB.exists():
        raise SystemExit(f"encounter.db not found at {DB}. Run `make all` first.")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT * FROM encounter_trials ORDER BY trial_id")
    cols = [d[0] for d in cur.description]
    trials = [dict(zip(cols, r)) for r in cur.fetchall()]

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "encounter.db (encounter-pipeline)",
        "trial_count": len(trials),
        "trials": [],
    }

    for trial in trials:
        tid = trial["trial_id"]

        # Arms keyed by arm_id
        cur.execute("SELECT * FROM encounter_arms WHERE trial_id=? ORDER BY arm_id", (tid,))
        arm_cols = [d[0] for d in cur.description]
        arms = {r[arm_cols.index("arm_id")]: dict(zip(arm_cols, r)) for r in cur.fetchall()}

        # Predictions for this trial
        cur.execute("SELECT * FROM encounter_predictions WHERE trial_id=? ORDER BY prediction_id", (tid,))
        pred_cols = [d[0] for d in cur.description]
        predictions = []
        for row in cur.fetchall():
            p = dict(zip(pred_cols, row))
            exp_arm = arms.get(p["experimental_arm_id"], {})
            ctrl_arm = arms.get(p["control_arm_id"], {})

            # Score (if any)
            cur.execute("SELECT * FROM encounter_scores WHERE prediction_id=?", (p["prediction_id"],))
            score_cols = [d[0] for d in cur.description]
            score_row = cur.fetchone()
            score = dict(zip(score_cols, score_row)) if score_row else None

            predictions.append({
                "prediction_id": p["prediction_id"],
                "experimental_arm": exp_arm.get("arm_label"),
                "experimental_combo": exp_arm.get("drug_combo"),
                "control_arm": ctrl_arm.get("arm_label"),
                "control_combo": ctrl_arm.get("drug_combo"),
                "direction": p["direction"],
                "confidence": p["confidence"],
                "metric": p["metric"],
                "predicted_value": p["predicted_value"],
                "predicted_range_low": p["predicted_range_low"],
                "predicted_range_high": p["predicted_range_high"],
                "structural_reason": p["structural_reason"],
                "falsifier": p["falsifier"],
                "method": p["method"],
                "prediction_date": p["prediction_date"],
                "score": score,
            })

        # Readout for this trial (most recent)
        cur.execute("SELECT * FROM encounter_readouts WHERE trial_id=? ORDER BY readout_date DESC LIMIT 1", (tid,))
        ro_cols = [d[0] for d in cur.description]
        ro_row = cur.fetchone()
        readout = dict(zip(ro_cols, ro_row)) if ro_row else None

        output["trials"].append({
            "trial_id": tid,
            "website_slug": TRIAL_TO_SLUG.get(tid),
            "trial_name": trial["trial_name"],
            "nct_id": trial["nct_id"],
            "sponsor": trial["sponsor"],
            "indication": trial["indication"],
            "n_target": trial["n_target"],
            "primary_endpoint": trial["primary_endpoint"],
            "status": trial["status"],
            "domain_id": trial["domain_id"],
            "stage_id": trial["stage_id"],
            "predictions": predictions,
            "readout": readout,
        })

    OUT.write_text(json.dumps(output, indent=2))
    print(f"Wrote {OUT}")
    print(f"  trials: {len(output['trials'])}")
    print(f"  predictions: {sum(len(t['predictions']) for t in output['trials'])}")
    print(f"  readouts: {sum(1 for t in output['trials'] if t['readout'])}")
    conn.close()


if __name__ == "__main__":
    main()
