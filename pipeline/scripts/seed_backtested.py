"""seed_backtested.py — Add the 4 historical confirmed hits as backtested trials.

KeyVibe-006 (Dec 2024 discontinuation), LATIFY (Dec 2025 missed primary OS),
TiNivo-2 (Sept 2024 ESMO), and STAR-221 (Dec 2025 discontinuation — already
in encounter_trials but needs to be marked as having a readout).

For each:
  1. Add trial to encounter_trials (if not already there) with discontinued status
  2. Add arms
  3. Add a readout row with the verified outcome
  4. Add a backtested prediction with prediction_date set to TODAY (after the
     known readout date) so the scorer correctly classifies as backtested.
     Backtested = prediction made AFTER outcome is already known.
"""
import sqlite3
import json
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).parent
_DATA = _HERE.parent / "data"

conn = sqlite3.connect(str(_DATA / 'encounter.db'))
cur = conn.cursor()


def add_trial(trial_id, nct, name, sponsor, indication, domain, stage, n,
              endpoint, status, source, notes=''):
    cur.execute("""INSERT OR REPLACE INTO encounter_trials (
        trial_id, nct_id, trial_name, sponsor, indication,
        domain_id, stage_id, n_target, primary_endpoint,
        status, metadata_verified_date, metadata_verified_source, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
        trial_id, nct, name, sponsor, indication, domain, stage, n, endpoint,
        status, '2026-04-10', source, notes
    ))


def add_arm(trial_id, label, role, combo, description=''):
    cur.execute("""INSERT INTO encounter_arms (trial_id, arm_label, arm_role, drug_combo, description)
                   VALUES (?, ?, ?, ?, ?)""", (trial_id, label, role, combo, description))
    return cur.lastrowid


def add_readout(trial_id, readout_date, source, metric, observed_value,
                outcome, notes=''):
    cur.execute("""INSERT INTO encounter_readouts (
        trial_id, readout_date, readout_source, metric, observed_value, outcome, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?)""", (
        trial_id, readout_date, source, metric, observed_value, outcome, notes
    ))
    return cur.lastrowid


def add_backtested_prediction(trial_id, exp_arm_id, ctrl_arm_id, direction,
                              metric, predicted_value, structural_reason,
                              falsifier, analog_trials, prediction_date):
    """Backtested predictions: prediction_date is set to TODAY (after the
    known readout). The scorer classifies these as backtested via:
       prediction_date >= readout_date → backtested
       prediction_date < readout_date → prospective
    """
    trace = {
        'mode': 'backtested',
        'method': 'structural_class_argument',
        'note': 'Backtested prediction: framework structural argument applied retrospectively to trial with known outcome. The directional call is correct because the framework correctly identifies the class-level pattern (TIGIT failure, ATR/PARP+ICI failure, etc), but the exact magnitude was not derived from formula.predict_orr() at this time.',
    }
    cur.execute("""INSERT INTO encounter_predictions (
        trial_id, experimental_arm_id, control_arm_id,
        direction, confidence, metric,
        predicted_value, predicted_range_low, predicted_range_high,
        population_held_in, bottleneck_position, bottleneck_description,
        coverage_analysis, structural_reason, falsifier,
        method, method_trace, analog_trials,
        prediction_date, prediction_session
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
        trial_id, exp_arm_id, ctrl_arm_id, direction, 'high', metric,
        predicted_value, None, None,
        'Conservation', 14, 'Metastatic 1L (Conservation regime)',
        'Class-level structural argument', structural_reason, falsifier,
        'backtested', json.dumps(trace), json.dumps(analog_trials),
        prediction_date, 'backtest_2026_04_10'
    ))
    return cur.lastrowid


# ─── KeyVibe-006: vibostolimab+pembro adj NSCLC stage III consolidation ───
# Discontinued Dec 16, 2024 for futility (per Merck press release)
add_trial(
    'keyvibe_006', 'NCT05298423', 'KeyVibe-006', 'Merck',
    'Stage III unresectable NSCLC consolidation post-cCRT',
    'nsclc', 'adj', 935, 'PFS', 'discontinued_futility',
    'Merck press release Dec 16, 2024; verification ledger 2026-04-10',
    'Verified discontinued Dec 16, 2024 — TIGIT class failure'
)
kv6_exp = add_arm('keyvibe_006', 'vibo_pembro', 'experimental',
                  'vibostolimab+pembrolizumab',
                  'Anti-TIGIT (vibostolimab) + anti-PD-1 (pembro) consolidation after definitive cCRT')
kv6_ctrl = add_arm('keyvibe_006', 'durva_pacific', 'control', 'durvalumab',
                   'PACIFIC standard durvalumab consolidation')
add_readout('keyvibe_006', '2024-12-16', 'Merck press release Dec 16, 2024',
            'PFS', None, 'discontinued_futility',
            'Discontinued for futility per Merck announcement; full data pending publication')
add_backtested_prediction(
    'keyvibe_006', kv6_exp, kv6_ctrl, 'FAIL', 'PFS', None,
    'TIGIT class structural failure: anti-TIGIT in Construction (sp=1 cross priming) does not productively combine with PD-1 in Conservation regime tumours. The class precedent across Roche (4 SKYSCRAPER trials), Merck (5 KeyVibe trials), Gilead/Arcus (STAR-221), and BeiGene (AdvanTIG-302) is 11/11 Phase 3 failures. KeyVibe-006 is the 6th of these.',
    'PFS HR < 0.85 in vibo+pembro arm at primary readout would refute FAIL.',
    [{'name': 'SKYSCRAPER-01 NSCLC', 'role': 'class_precedent'},
     {'name': 'KeyVibe-003 NSCLC', 'role': 'sponsor_class_precedent'},
     {'name': 'KeyVibe-008 SCLC', 'role': 'sponsor_class_precedent'}],
    datetime.now(timezone.utc).isoformat()  # today (after readout)
)

# ─── LATIFY: ceralasertib+durva NSCLC met 2L+ ───
# n=594, missed primary OS Dec 22, 2025
add_trial(
    'latify', 'NCT05450692', 'LATIFY', 'AstraZeneca',
    '2L+ EGFRm/ALK+ NSCLC, ATR inhibitor + ICI',
    'nsclc', 'met_2l', 594, 'OS', 'discontinued_futility',
    'AstraZeneca pipeline update; verification ledger 2026-04-10',
    'Phase 3 ATR+ICI in pre-treated NSCLC failed primary OS Dec 22, 2025'
)
lat_exp = add_arm('latify', 'cera_durva', 'experimental',
                  'ceralasertib+durvalumab',
                  'ATR inhibitor (ceralasertib) + anti-PD-L1 (durvalumab)')
lat_ctrl = add_arm('latify', 'doce', 'control', 'docetaxel',
                   'Standard 2L+ NSCLC docetaxel chemotherapy')
add_readout('latify', '2025-12-22', 'AstraZeneca Dec 22, 2025 update',
            'OS', None, 'failed_primary',
            'Missed primary OS endpoint at primary analysis')
add_backtested_prediction(
    'latify', lat_exp, lat_ctrl, 'FAIL', 'OS', None,
    'ATR (DDR) + ICI structural failure: ATR inhibition is L4 (genomic/molecular DNA repair) Construction Blocker, ICI is L3 Conservation effector. The Bliss combination of these two layers in Conservation-dominated metastatic 2L+ does not produce additive benefit when the upstream tumour has already escaped immune surveillance. Without HRD selection or genomic stratification, ATR class adds nothing — analogous to PARP+ICI in unselected tumours (KEYLYNK-008/010/PROpel pattern).',
    'OS HR < 0.85 would refute FAIL.',
    [{'name': 'KEYLYNK-008 NSCLC', 'role': 'parp_ici_class_precedent'},
     {'name': 'KEYLYNK-010 mCRPC', 'role': 'parp_ici_class_precedent'}],
    datetime.now(timezone.utc).isoformat()
)

# ─── TiNivo-2: tivozanib+nivolumab 2L+ RCC ───
# n=343, AVEO/LG Chem, ESMO Sep 2024 readout, missed
add_trial(
    'tinivo_2', 'NCT04987203', 'TiNivo-2', 'AVEO Oncology / LG Chem',
    '2L+ RCC, TKI + nivolumab vs TKI alone',
    'rcc', 'met_2l', 343, 'PFS', 'failed_primary',
    'AVEO press release July 18, 2024; ESMO September 2024',
    'Phase 3 of tivozanib + nivolumab vs tivozanib mono in 2L+ RCC after prior ICI'
)
tn_exp = add_arm('tinivo_2', 'tivo_nivo', 'experimental',
                 'tivozanib+nivolumab',
                 'VEGF TKI + anti-PD-1 in IO-pretreated RCC')
tn_ctrl = add_arm('tinivo_2', 'tivo_mono', 'control', 'tivozanib',
                  'Tivozanib monotherapy')
add_readout('tinivo_2', '2024-09-15', 'ESMO 2024 / AVEO July 18 release',
            'PFS', None, 'failed_primary',
            'Missed primary PFS endpoint vs tivozanib alone')
add_backtested_prediction(
    'tinivo_2', tn_exp, tn_ctrl, 'FAIL', 'PFS', None,
    'IO continuation after IO failure structural argument: in 2L+ RCC after prior ICI exposure, the tumour has already escaped immune surveillance (Conservation regime, depth=2 → depth=3). Re-introducing PD-1 blockade in this setting adds nothing structural beyond the TKI alone. The same pattern was confirmed by CONTACT-03 (atezo+cabo vs cabo in IO-pretreated RCC, also failed). The framework correctly predicts FAIL for any "ICI continuation after ICI failure" trial in Conservation-dominated indications.',
    'PFS HR < 0.85 would refute FAIL.',
    [{'name': 'CONTACT-03', 'role': 'identical_class_precedent'}],
    datetime.now(timezone.utc).isoformat()
)

# Note: STAR-221 is already in encounter_trials as discontinued.
# Add the readout and backtested prediction for STAR-221.
cur.execute("SELECT arm_id, arm_role FROM encounter_arms WHERE trial_id='star_221'")
star_arms = {role: aid for aid, role in cur.fetchall()}
star_exp = star_arms.get('experimental')
star_ctrl = star_arms.get('control')
add_readout('star_221', '2025-12-12', 'Arcus/Gilead Dec 12, 2025 press release',
            'OS', None, 'discontinued_futility',
            'Discontinued for futility — independent DMC recommendation')
# STAR-221 already has its mode_a_calibrated FAIL prediction. Don't double-add.

conn.commit()

print("Backtested seed complete:")
print(f"  trials:    {cur.execute('SELECT COUNT(*) FROM encounter_trials').fetchone()[0]}")
print(f"  arms:      {cur.execute('SELECT COUNT(*) FROM encounter_arms').fetchone()[0]}")
print(f"  predictions: {cur.execute('SELECT COUNT(*) FROM encounter_predictions').fetchone()[0]}")
print(f"  readouts:  {cur.execute('SELECT COUNT(*) FROM encounter_readouts').fetchone()[0]}")

# List all readouts
print("\nReadouts:")
cur.execute("SELECT trial_id, readout_date, outcome FROM encounter_readouts ORDER BY readout_date")
for r in cur.fetchall():
    print(f"  {r[0]:18s} {r[1]:12s} {r[2]}")

conn.close()
