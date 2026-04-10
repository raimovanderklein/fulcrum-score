"""seed_trials.py — populate encounter_trials and encounter_arms from verified data.

Sources:
  - encounter-bio/data/reports.json (live site data, metadata-verified)
  - Verification ledger findings from this session (corrections not yet applied to site)

Idempotent: re-running replaces existing trials with same trial_id.
Does NOT write predictions — that's the job of make_predictions.py.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

HERE = Path(__file__).parent
REPO = HERE.parent
DATA = REPO / "data"
DATA.mkdir(exist_ok=True)
DB_PATH = DATA / "encounter.db"

# Trial definitions, grounded in the verification ledger (2026-04-10 pass).
# Every field here has been independently verified this session.
# Corrections from v1/v2 are applied here so the database is the canonical version.

TRIALS = [
    {
        "trial_id": "volga",
        "nct_id": "NCT04960709",
        "trial_name": "VOLGA",
        "sponsor": "AstraZeneca",
        "indication": "Muscle-invasive bladder cancer, cisplatin-ineligible, perioperative",
        "domain_id": "urothelial",
        "stage_id": "neo",
        "n_target": 677,  # CORRECTED from v1's 830
        "arm_count": 3,
        "primary_endpoint": "pCR",
        "estimated_readout": "2026-04",
        "status": "active",
        "metadata_verified_date": "2026-04-10",
        "metadata_verified_source": "ClinicalTrials.gov NCT04960709; ESMO 2024 safety run-in (pCR 6/17=35%)",
        "site_slug": "volga-bladder-periop",
        "notes": "ESMO 2024 safety run-in reported pCR 6/17 = 35%, below v1's ≥50% floor. v1 had n=830; corrected to 677.",
        "arms": [
            {
                "label": "triplet",
                "role": "experimental",
                "drug_combo": "durvalumab+tremelimumab+enfortumab_vedotin",
                "description": "Neoadjuvant durvalumab + tremelimumab + EV, then cystectomy, then adjuvant durvalumab + tremelimumab"
            },
            {
                "label": "duplet",
                "role": "experimental",
                "drug_combo": "durvalumab+enfortumab_vedotin",
                "description": "Neoadjuvant durvalumab + EV, then cystectomy, then adjuvant durvalumab"
            },
            {
                "label": "control",
                "role": "control",
                "drug_combo": "surgery_only",
                "description": "Radical cystectomy alone (no neoadjuvant systemic therapy)"
            }
        ]
    },
    {
        "trial_id": "harmony_melanoma",
        "nct_id": "NCT05352672",
        "trial_name": "Harmony Melanoma",
        "sponsor": "Regeneron Pharmaceuticals",
        "indication": "1L unresectable / metastatic melanoma",
        "domain_id": "melanoma",
        "stage_id": "met_1l",
        "n_target": 1590,
        "arm_count": 3,
        "primary_endpoint": "PFS",
        "estimated_readout": "2026-H2",
        "status": "enrollment_closed",
        "metadata_verified_date": "2026-04-10",
        "metadata_verified_source": "ClinicalTrials.gov NCT05352672; Melanoma Research Alliance",
        "site_slug": "harmony-melanoma-fianlimab",
        "notes": "Three-arm trial with cemiplimab monotherapy as critical-test arm. If Arm C ≈ Arm A, LAG-3 attribution is confirmed; if Arm C ≈ Arm B, the win is carried by cemi alone.",
        "arms": [
            {
                "label": "fianlimab_cemiplimab",
                "role": "experimental",
                "drug_combo": "fianlimab+cemiplimab",
                "description": "Fianlimab (anti-LAG-3) + cemiplimab (anti-PD-1) FDC"
            },
            {
                "label": "pembrolizumab",
                "role": "control",
                "drug_combo": "pembrolizumab",
                "description": "Pembrolizumab monotherapy (current SOC)"
            },
            {
                "label": "cemiplimab_mono",
                "role": "critical_test",
                "drug_combo": "cemiplimab",
                "description": "Cemiplimab monotherapy — tests whether the win comes from LAG-3 addition or cemiplimab alone"
            }
        ]
    },
    {
        "trial_id": "energize",
        "nct_id": "NCT03661320",
        "trial_name": "ENERGIZE",
        "sponsor": "Bristol Myers Squibb",
        "indication": "Cisplatin-eligible muscle-invasive bladder cancer, perioperative",
        "domain_id": "urothelial",
        "stage_id": "neo",
        "n_target": 1200,
        "arm_count": 3,
        "primary_endpoint": "EFS",
        "estimated_readout": "2026-06",
        "status": "active",
        "metadata_verified_date": "2026-04-10",
        "metadata_verified_source": "ClinicalTrials.gov NCT03661320",
        "site_slug": "energize-bladder-periop",
        "notes": "Three-arm: gem/cis vs gem/cis+nivo vs gem/cis+nivo+linrodostat. Tests both PD-1 addition AND IDO1 addition. Critical test for IDO1 is (B > A) AND (C ≈ B).",
        "arms": [
            {
                "label": "gemcis_nivo_linrodostat",
                "role": "experimental",
                "drug_combo": "gemcitabine+cisplatin+nivolumab+linrodostat",
                "description": "Gem/cis + nivo + IDO1 inhibitor (Arm C)"
            },
            {
                "label": "gemcis_nivo",
                "role": "critical_test",
                "drug_combo": "gemcitabine+cisplatin+nivolumab",
                "description": "Gem/cis + nivo (Arm B) — tests whether IDO1 adds anything on top"
            },
            {
                "label": "gemcis",
                "role": "control",
                "drug_combo": "gemcitabine+cisplatin",
                "description": "Gem/cis alone (Arm A)"
            }
        ]
    },
    {
        "trial_id": "imbrave251",
        "nct_id": "NCT04770896",
        "trial_name": "IMbrave251",
        "sponsor": "Hoffmann-La Roche",
        "indication": "2L HCC after atezolizumab + bevacizumab",
        "domain_id": "hcc",
        "stage_id": "met_2l",
        "n_target": 554,
        "arm_count": 2,
        "primary_endpoint": "OS",
        "estimated_readout": "2026",
        "status": "active",
        "metadata_verified_date": "2026-04-10",
        "metadata_verified_source": "ClinicalTrials.gov NCT04770896",
        "site_slug": "imbrave251-hcc-2l",
        "notes": "Tests PD-(L)1 continuation beyond progression on atezo+bev. Structural call: same step already failed, no coverage gain.",
        "arms": [
            {
                "label": "atezo_tki",
                "role": "experimental",
                "drug_combo": "atezolizumab+lenvatinib_or_sorafenib",
                "description": "Atezolizumab + lenvatinib or sorafenib"
            },
            {
                "label": "tki_mono",
                "role": "control",
                "drug_combo": "lenvatinib_or_sorafenib",
                "description": "Lenvatinib or sorafenib monotherapy"
            }
        ]
    },
    {
        "trial_id": "keylynk_012",
        "nct_id": "NCT04380636",
        "trial_name": "KEYLYNK-012",
        "sponsor": "Merck",
        "indication": "Stage III unresectable NSCLC",
        "domain_id": "nsclc",
        "stage_id": "adj",
        "n_target": 870,
        "arm_count": 3,
        "primary_endpoint": "PFS",
        "estimated_readout": "2026-07",
        "status": "active",
        "metadata_verified_date": "2026-04-10",
        "metadata_verified_source": "ClinicalTrials.gov NCT04380636",
        "site_slug": "keylynk-012-nsclc-3",
        "notes": "Tests pembro consolidation ± olaparib vs durvalumab consolidation (PACIFIC regimen) after concurrent CRT. KEYLYNK-008 (1L metastatic squamous NSCLC) already failed April 2024 for the PARP+PD-1 combo concept.",
        "arms": [
            {
                "label": "pembro_olaparib",
                "role": "experimental",
                "drug_combo": "pembrolizumab+olaparib",
                "description": "CRT → pembro + olaparib consolidation"
            },
            {
                "label": "pembro_consolidation",
                "role": "critical_test",
                "drug_combo": "pembrolizumab",
                "description": "CRT → pembro consolidation alone — tests whether olaparib adds anything"
            },
            {
                "label": "durvalumab_pacific",
                "role": "control",
                "drug_combo": "durvalumab",
                "description": "CRT → durvalumab consolidation (PACIFIC SOC)"
            }
        ]
    },
    {
        "trial_id": "star_221",
        "nct_id": "NCT05568095",
        "trial_name": "STAR-221",
        "sponsor": "Arcus Biosciences / Gilead Sciences",
        "indication": "1L gastric / GEJ / esophageal adenocarcinoma",
        "domain_id": "gastric",
        "stage_id": "met_1l",
        "n_target": 1050,
        "arm_count": 2,
        "primary_endpoint": "OS",
        "estimated_readout": "2025-12-12",
        "status": "discontinued_futility",
        "metadata_verified_date": "2026-04-10",
        "metadata_verified_source": "Arcus press release Dec 12 2025",
        "site_slug": "star-221-tigit-gastric",
        "notes": "Discontinued Dec 12 2025 for futility. This is a BACKTESTED hit — framework was applied in v1 (published Apr 3 2026) after the discontinuation was already public. Used here as a scored historical trial for the TIGIT class argument.",
        "arms": [
            {
                "label": "dom_zim_chemo",
                "role": "experimental",
                "drug_combo": "domvanalimab+zimberelimab+chemo",
                "description": "Domvanalimab (TIGIT) + zimberelimab (PD-1) + chemotherapy"
            },
            {
                "label": "nivo_chemo",
                "role": "control",
                "drug_combo": "nivolumab+chemo",
                "description": "Nivolumab + chemotherapy (SOC)"
            }
        ]
    },
]


def upsert_trial(conn, trial):
    """Insert or replace a trial and its arms. Returns the trial_id."""
    cur = conn.cursor()
    
    # Delete existing arms and the trial (cascade-style, no FK enforcement)
    cur.execute("DELETE FROM encounter_arms WHERE trial_id=?", (trial["trial_id"],))
    cur.execute("DELETE FROM encounter_trials WHERE trial_id=?", (trial["trial_id"],))
    
    trial_cols = ["trial_id", "nct_id", "trial_name", "sponsor", "indication",
                  "domain_id", "stage_id", "n_target", "arm_count", "primary_endpoint",
                  "estimated_readout", "status", "metadata_verified_date",
                  "metadata_verified_source", "site_slug", "notes"]
    placeholders = ",".join(["?"] * len(trial_cols))
    cur.execute(
        f"INSERT INTO encounter_trials ({','.join(trial_cols)}) VALUES ({placeholders})",
        tuple(trial.get(c) for c in trial_cols)
    )
    
    for arm in trial["arms"]:
        cur.execute(
            "INSERT INTO encounter_arms (trial_id, arm_label, arm_role, drug_combo, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (trial["trial_id"], arm["label"], arm["role"], arm["drug_combo"], arm.get("description"))
        )
    
    return trial["trial_id"]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = OFF")
    
    print(f"Seeding {len(TRIALS)} trials into {DB_PATH}\n")
    for trial in TRIALS:
        upsert_trial(conn, trial)
        n_arms = len(trial["arms"])
        print(f"  ✓ {trial['trial_id']:20s} | {trial['trial_name']:25s} | {n_arms} arms | status={trial['status']}")
    
    conn.commit()
    
    # Summary
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM encounter_trials")
    n_trials = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM encounter_arms")
    n_arms_total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM encounter_trials WHERE status='discontinued_futility'")
    n_readout = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM encounter_trials WHERE status IN ('active','enrollment_closed')")
    n_pending = cur.fetchone()[0]
    
    print(f"\nSummary:")
    print(f"  Total trials:    {n_trials}")
    print(f"  Total arms:      {n_arms_total}")
    print(f"  Readout known:   {n_readout}")
    print(f"  Readout pending: {n_pending}")
    
    conn.close()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
