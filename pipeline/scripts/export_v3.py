"""export_v3.py — Generate v3 scorecard markdown directly from encounter.db.

Reads the database and emits markdown with methodology
hits, prospective predictions, and methodology limits.

Output: ../v3_scorecard.md
"""
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path
# ─── Path resolution: locate sibling files relative to this script ───
import os as _os

# Single source of truth for Zenodo DOIs.
# v1/v2/v3 were deleted on 2026-04-10. The scorecard currently lives on encounter.bio
# only. When re-published to Zenodo, set ZENODO_CONCEPT_DOI and ZENODO_VERSION_DOI
# from the real Zenodo sidebar — do NOT invent values.
ZENODO_CONCEPT_DOI = None
ZENODO_VERSION_DOI = None

_HERE = Path(_os.path.dirname(_os.path.abspath(__file__)))
_REPO = _HERE.parent
_DATA = _REPO / 'data'


DB = _DATA / 'encounter.db'
OUT = _REPO / 'docs' / 'v3_scorecard.md'


def get_trial(cur, trial_id):
    cur.execute("SELECT * FROM encounter_trials WHERE trial_id=?", (trial_id,))
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    return dict(zip(cols, row)) if row else None


def get_arms_dict(cur, trial_id):
    cur.execute("SELECT * FROM encounter_arms WHERE trial_id=? ORDER BY arm_id", (trial_id,))
    cols = [d[0] for d in cur.description]
    out = {}
    for r in cur.fetchall():
        d = dict(zip(cols, r))
        out[d['arm_id']] = d
    return out


def get_predictions(cur, trial_id):
    cur.execute("SELECT * FROM encounter_predictions WHERE trial_id=? ORDER BY prediction_id", (trial_id,))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def get_readout(cur, trial_id):
    cur.execute("SELECT * FROM encounter_readouts WHERE trial_id=? ORDER BY readout_date DESC LIMIT 1", (trial_id,))
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    return dict(zip(cols, row)) if row else None


def get_score(cur, prediction_id):
    cur.execute("SELECT * FROM encounter_scores WHERE prediction_id=?", (prediction_id,))
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    return dict(zip(cols, row)) if row else None


def render_trial_section(cur, trial_id):
    trial = get_trial(cur, trial_id)
    arms = get_arms_dict(cur, trial_id)
    predictions = get_predictions(cur, trial_id)
    readout = get_readout(cur, trial_id)

    out = []
    out.append(f"### {trial['trial_name']}")
    out.append("")
    out.append(f"- **NCT:** {trial['nct_id']}")
    out.append(f"- **Sponsor:** {trial['sponsor']}")
    out.append(f"- **Indication:** {trial['indication']}")
    out.append(f"- **Domain / stage (GG taxonomy):** `{trial['domain_id']}` / `{trial['stage_id']}`")
    out.append(f"- **n target:** {trial['n_target']}")
    out.append(f"- **Primary endpoint:** {trial['primary_endpoint']}")
    out.append(f"- **Status:** {trial['status']}")
    out.append("")

    out.append("**Arms:**")
    out.append("")
    for arm in arms.values():
        out.append(f"- _{arm['arm_role']}_ — **{arm['arm_label']}**: `{arm['drug_combo']}`")
    out.append("")

    if readout:
        out.append(f"**Readout (already known):** {readout['readout_date']} — `{readout['outcome']}`")
        if readout.get('notes'):
            out.append("")
            out.append(f"> {readout['notes']}")
        out.append("")

    out.append("**Framework predictions:**")
    out.append("")
    for p in predictions:
        exp_arm = arms.get(p['experimental_arm_id'], {}).get('arm_label', '?')
        ctrl_arm = arms.get(p['control_arm_id'], {}).get('arm_label', '?')
        score = get_score(cur, p['prediction_id'])

        out.append(f"#### {exp_arm} vs {ctrl_arm}")
        out.append("")
        out.append(f"- **Direction:** **{p['direction']}**")
        out.append(f"- **Confidence:** {p['confidence']}")
        out.append(f"- **Metric:** {p['metric']}")
        if p['predicted_value'] is not None:
            range_str = ""
            if p['predicted_range_low'] is not None and p['predicted_range_high'] is not None:
                range_str = f" (range {p['predicted_range_low']}–{p['predicted_range_high']})"
            out.append(f"- **Predicted value:** {p['predicted_value']}{range_str}")
        out.append(f"- **Method:** `{p['method']}`")
        out.append(f"- **Falsifier:** {p['falsifier']}")
        if score:
            out.append(f"- **Score:** `{score['hit_type']}`, direction_correct={score['direction_correct']}")
        out.append("")
        out.append(f"_Reasoning:_ {p['structural_reason']}")
        out.append("")

    return '\n'.join(out)


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM encounter_trials")
    n_trials = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM encounter_predictions")
    n_predictions = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM encounter_readouts")
    n_readouts = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM encounter_scores")
    n_scored = cur.fetchone()[0]
    cur.execute("SELECT hit_type, COUNT(*) FROM encounter_scores GROUP BY hit_type")
    hit_breakdown = dict(cur.fetchall())

    today = datetime.now(timezone.utc).strftime('%B %d, %Y')

    md = []
    md.append("# Encounter Living Scorecard")
    md.append("")
    md.append(f"_Generated from `encounter.db` on {today}._")
    md.append("")
    if ZENODO_CONCEPT_DOI:
        md.append(f"**Concept DOI:** [{ZENODO_CONCEPT_DOI}](https://doi.org/{ZENODO_CONCEPT_DOI})")
    else:
        md.append("**Hosted at:** https://encounter.bio · not currently archived on Zenodo")
    md.append("")
    if ZENODO_VERSION_DOI:
        md.append(f"**Version DOI:** [{ZENODO_VERSION_DOI}](https://doi.org/{ZENODO_VERSION_DOI})")
    md.append("")
    md.append("## Contact")
    md.append("")
    md.append("- **Web:** https://encounter.bio")
    md.append("- **Contact:** https://encounter.bio/contact")
    md.append("- **Author:** Raimo van der Klein, founder of Encounter")
    md.append("- **Framework:** Generative Geometry (van der Klein, 2026)")
    md.append("")
    md.append("")
    md.append("## Track record at a glance")
    md.append("")
    md.append(f"- **Trials catalogued:** {n_trials}")
    md.append(f"- **Framework predictions persisted:** {n_predictions}")
    md.append(f"- **Trials with readouts:** {n_readouts}")
    md.append(f"- **Scored predictions:** {n_scored}")
    md.append("")
    md.append("**Honest hit breakdown:**")
    md.append("")
    if hit_breakdown:
        for k, v in sorted(hit_breakdown.items()):
            md.append(f"- {k}: {v}")
    else:
        md.append("- No predictions have scored yet. All current entries are prospective, awaiting readout.")
    md.append("")
    md.append(f"**Prospective predictions awaiting readout:** {n_trials}")
    md.append("")
    md.append("**Fully prospective hits (so far):** 0. No trials in the current catalogue have read out yet.")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Methodology")
    md.append("")
    md.append("Predictions are generated by `formula.predict_orr(domain, combo, stage)` from the Generative Geometry framework's single source of truth (`formula.py` v13). The function takes:")
    md.append("")
    md.append("- a **disease domain** (urothelial, melanoma, NSCLC, HCC, gastric, SCLC, etc.)")
    md.append("- a **drug combo** (an unordered set of agent IDs joined by `+`)")
    md.append("- a **treatment stage** (neoadjuvant, adjuvant, metastatic 1L/2L/3L+)")
    md.append("")
    md.append("And returns a predicted ORR with one of four method tiers:")
    md.append("")
    md.append("1. **Calibrated** — exact (domain, combo, stage) match in the calibration table back-calculated from 183 historical trials with observed ORRs.")
    md.append("2. **Stage-scaled** — same combo at a different stage; M transferred via the agent type model.")
    md.append("3. **Single-scaled** — single agent calibrated against any stage.")
    md.append("4. **Novel from components** — agent layer split (L3 immune, L4 molecular), Bliss independence within layer, cross-layer Bliss combine, clamped at the stage's depth resistance ceiling.")
    md.append("")
    md.append("For neoadjuvant trials, ORR is translated to pCR using the canonical ratio observed in EV-103 cohort H, NIAGARA, and KEYNOTE-B15 (pCR ≈ 0.55 × ORR for urothelial neoadjuvant; lower for gastric and NSCLC).")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Methodology benchmarks")
    md.append("")
    md.append("FULCRUM, the patient-level scoring function inside the framework, has been head-to-head benchmarked against the two largest published transcriptomic ICB prediction frameworks on their own data:")
    md.append("")
    md.append("| Comparison | Cohorts | FULCRUM AUC | Benchmark AUC | Method |")
    md.append("| --- | --- | --- | --- | --- |")
    md.append("| vs **EXPRESSO-B** (melanoma) | 8 | **0.710** | 0.710 | 5-gene ratio vs whole-transcriptome LASSO |")
    md.append("| vs **EXPRESSO-T** (non-melanoma) | 7 | **0.768** | 0.720 | 5-gene ratio vs whole-transcriptome LASSO |")
    md.append("| vs **TIME_ACT** (8 shared cohorts) | 8 | **0.825** | 0.794 | 5-gene ratio vs 66-gene unsupervised ssGSEA |")
    md.append("")
    md.append("EXPRESSO is Pal, Ruppin et al. 2025 (bioRxiv 10.1101/2025.10.24.684491v2). TIME_ACT is Mukherjee, Ruppin et al. 2025 (bioRxiv 10.1101/2025.06.27.661875v2).")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## Prospective predictions awaiting readout")
    md.append("")
    md.append("These six trials have not yet read out. The framework's predictions below are testable: each comes with a falsifier that, if observed at the actual readout, would refute the call.")
    md.append("")

    prospective_trials = ['volga', 'harmony_melanoma', 'energize', 'imbrave251', 'keylynk_012', 'dellphi_312']
    for tid in prospective_trials:
        md.append(render_trial_section(cur, tid))
        md.append("---")
        md.append("")

    md.append("## Methodology limits")
    md.append("")
    md.append("The following are known gaps in the current implementation:")
    md.append("")
    md.append("1. **Acquired resistance not modelled natively.** The base formula has no `prior_line_failure` modifier. For IMbrave251 (atezo continuation after atezo+bev failure), the raw `predict_orr` output is +15.4pp (WIN) because it treats the 2L combo as a novel structural combination. The final FAIL call comes from a class precedent override layered on top of the formula output, citing the IO-progression-after-progression literature. v4 should move this override into the formula itself via an explicit `prior_line_failure` penalty rather than handling it in the pipeline wrapper.")
    md.append("")
    md.append("2. **Depth-2 ceiling clamping.** For neoadjuvant indications at depth 2, most cross-layer immune+molecular combinations saturate against the depth resistance ceiling (~70–74%). Differentials must be read at the per-layer level, not the final clamped output.")
    md.append("")
    md.append("3. **ORR-to-pCR translation is fixed-ratio.** The 0.55 ratio for urothelial neoadjuvant is anchored to three trials. Trials testing novel combos may have different ORR-to-pCR ratios.")
    md.append("")
    md.append("4. **Calibration table scrubbing required.** Two evidence rows in the GG framework's `systems.db` (IMpower010, PEARLS/KEYNOTE-091) report `observed_orr=0` because their actual endpoint was DFS, not ORR. v3 uses a `safe_cal_table()` wrapper that filters them out.")
    md.append("")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## How to reproduce")
    md.append("")
    md.append("The encounter pipeline expects access to `formula.py` (v13) and the GG framework's `systems.db` calibration database.")
    md.append("")
    md.append("```")
    md.append("python3 seed_trials.py             # populate trial schema")
    md.append("python3 seed_dellphi312.py         # add DeLLphi-312")
    md.append("python3 make_predictions_all.py    # run formula.predict_orr against all trials")
    md.append("python3 score_predictions.py       # score predictions vs readouts")
    md.append("python3 export_v3.py               # regenerate this document")
    md.append("```")
    md.append("")
    md.append("Every prediction in `encounter.db` has a `method_trace` field with the full output of `formula.predict_orr` including the calibration table size, agent substitutions, per-layer ORRs, depth ceiling, and prediction date.")
    md.append("")

    out_text = '\n'.join(md)
    OUT.write_text(out_text)
    print(f"v3 markdown written to {OUT}")
    print(f"  size: {len(out_text)} chars, {out_text.count(chr(10))} lines")
    conn.close()


if __name__ == '__main__':
    main()
