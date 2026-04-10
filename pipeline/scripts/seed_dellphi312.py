"""Add DeLLphi-312 to encounter_trials and encounter_arms.

Verified metadata from trial verification ledger 2026-04-10:
- NCT07005128, Amgen, ~330 patients, 1L ES-SCLC
- Tarlatamab + durva + carbo+etoposide vs durva + carbo+etoposide
"""
import sqlite3
from pathlib import Path

_HERE = Path(__file__).parent
_DATA = _HERE.parent / "data"
conn = sqlite3.connect(str(_DATA / "encounter.db"))
cur = conn.cursor()

# Insert trial (idempotent)
cur.execute("""
INSERT OR REPLACE INTO encounter_trials (
    trial_id, nct_id, trial_name, sponsor, indication,
    domain_id, stage_id, n_target, arm_count, primary_endpoint,
    estimated_readout, status, metadata_verified_date, metadata_verified_source, site_slug, notes
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    'dellphi_312',
    'NCT07005128',
    'DeLLphi-312',
    'Amgen',
    '1L extensive-stage SCLC',
    'sclc',  # not in formula.py taxonomy yet — flag for Mode B
    'es_1l',
    330,
    2,
    'OS',
    '2027',  # Phase 3 active, no firm readout date yet
    'active',
    '2026-04-10',
    'Amgen DeLLphi-304 press releases (Jun 2025, Nov 2025); tarlatamabclinicaltrials.com; NEJM 2025 DeLLphi-304 paper',
    None,  # not on encounter.bio yet
    'Triplet+ vs control. DeLLphi-304 already proved tarlatamab in 2L ES-SCLC (HR 0.60) — DeLLphi-312 tests adding it to 1L chemo-IO backbone.'
))

# Remove existing arms if re-seeding
cur.execute("DELETE FROM encounter_arms WHERE trial_id='dellphi_312'")

# Control arm: standard 1L ES-SCLC chemo-IO
cur.execute("""
INSERT INTO encounter_arms (trial_id, arm_label, arm_role, drug_combo, description)
VALUES (?, ?, ?, ?, ?)
""", (
    'dellphi_312',
    'durva_carbo_etop',
    'control',
    'durvalumab+carboplatin+etoposide',
    'Standard 1L ES-SCLC induction (4 cycles) then durvalumab maintenance.'
))

# Experimental arm: add tarlatamab
cur.execute("""
INSERT INTO encounter_arms (trial_id, arm_label, arm_role, drug_combo, description)
VALUES (?, ?, ?, ?, ?)
""", (
    'dellphi_312',
    'tarla_durva_carbo_etop',
    'experimental',
    'tarlatamab+durvalumab+carboplatin+etoposide',
    'Tarlatamab added to standard 1L chemo-IO. Tarlatamab once D1 and D8 of cycle 1, then Q3W cycles 2-4, then Q2W maintenance.'
))

conn.commit()
print("DeLLphi-312 seeded.")
print(f"Trials in db: {cur.execute('SELECT COUNT(*) FROM encounter_trials').fetchone()[0]}")
print(f"Arms in db: {cur.execute('SELECT COUNT(*) FROM encounter_arms').fetchone()[0]}")
conn.close()
