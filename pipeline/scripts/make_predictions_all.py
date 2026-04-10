"""make_predictions_all.py — Generic Mode A prediction engine for all trials."""
import sqlite3
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
# ─── Path resolution: locate sibling files relative to this script ───
import os as _os
_HERE = Path(_os.path.dirname(_os.path.abspath(__file__)))
_REPO = _HERE.parent
_DATA = _REPO / 'data'


GG_SYSTEMS_DB = _DATA / 'gg_systems_workcopy.db'
ENCOUNTER_DB = _DATA / 'encounter.db'
FORMULA_PY_PATH = _HERE
sys.path.insert(0, str(FORMULA_PY_PATH))
import formula  # noqa: E402

PREDICTION_SESSION = f"v3_pipeline_{datetime.now(timezone.utc).strftime('%Y_%m_%d')}"


def now_iso():
    return datetime.now(timezone.utc).isoformat()


DRUG_TO_GG_AGENT = {
    'urothelial': {
        'enfortumab_vedotin': 'ev', 'enfortumab vedotin': 'ev',
        'pembrolizumab': 'pembro_bl', 'cisplatin': 'cispl_bl',
        'gemcitabine': 'gem_bl', 'erdafitinib': 'erda',
        'durvalumab': 'durva', 'tremelimumab': 'treme',
        'nivolumab': 'nivo_bl', 'atezolizumab': 'pembro_bl',
        'linrodostat': 'linro_bl', 'surgery_only': None,
    },
    'gastric': {
        'oxaliplatin': 'oxa_ga', '5-fu': 'fu_ga', 'capecitabine': 'fu_ga',
        '5-fluorouracil': 'fu_ga', 'fluorouracil': 'fu_ga',
        'nivolumab': 'nivo_ga', 'trastuzumab': 'trast_ga',
        'ramucirumab': 'ramu_ga', 'paclitaxel': 'pacli_ga',
        'cisplatin': 'cispl_ga', 'chemo': 'oxa_ga+fu_ga',
        'domvanalimab': 'domv_ga', 'zimberelimab': 'zimb_ga',
    },
    'melanoma': {
        'nivolumab': 'nivo', 'pembrolizumab': 'pembro_m',
        'ipilimumab': 'ipi', 'cemiplimab': 'cemi_m',
        'fianlimab': 'fian_m', 'relatlimab': 'rela_m',
    },
    'nsclc': {
        'pembrolizumab': 'pembro_l', 'nivolumab': 'nivo_l',
        'atezolizumab': 'atezo', 'durvalumab': 'durva',
        'olaparib': 'ola_l',
    },
    'hcc': {
        'sorafenib': 'soraf', 'lenvatinib': 'lenva_h',
        'cabozantinib': 'cabo_h', 'regorafenib': 'rego_h',
        'atezolizumab': 'atezo_h', 'durvalumab': 'durva_h',
        'nivolumab': 'nivo_h', 'pembrolizumab': 'pembro_h',
        'tremelimumab': 'treme_h', 'ipilimumab': 'ipi_h',
        'bevacizumab': 'bev_h',
        'lenvatinib_or_sorafenib': 'lenva_h',
    },
    'sclc': {
        'carboplatin': 'carbo_s', 'etoposide': 'etop_s',
        'atezolizumab': 'atezo_s', 'durvalumab': 'durva_s',
        'topotecan': 'topo_s', 'lurbinectedin': 'lurbi_s',
        'tarlatamab': 'tarla_s',
    },
}


ORR_TO_ENDPOINT = {
    'urothelial': {'neo': ('pCR', 0.55)},
}


def parse_combo(s):
    return [d.strip().lower() for d in s.split('+')]


def map_combo_to_gg(domain_id, drug_list):
    mapping = DRUG_TO_GG_AGENT.get(domain_id, {})
    mapped, missing = [], []
    for drug in drug_list:
        if drug not in mapping:
            missing.append(drug)
            continue
        agent = mapping[drug]
        if agent is None:
            continue
        if '+' in str(agent):
            for sub_a in agent.split('+'):
                mapped.append(sub_a)
        else:
            mapped.append(agent)
    return {'mapped': mapped, 'missing': missing}


def get_trial(conn, trial_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM encounter_trials WHERE trial_id=?", (trial_id,))
    cols = [d[0] for d in cur.description]
    row = cur.fetchone()
    return dict(zip(cols, row)) if row else None


def get_arms(conn, trial_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM encounter_arms WHERE trial_id=? ORDER BY arm_id", (trial_id,))
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def predict_arm(gg_conn, domain, stage, drug_combo, cal_table):
    drugs = parse_combo(drug_combo)
    if drug_combo == 'surgery_only':
        return {'orr': None, 'layer_orrs': {}, 'method': 'no_treatment',
                'note': 'surgery only', 'missing': []}
    mapping = map_combo_to_gg(domain, drugs)
    if not mapping['mapped']:
        return {'error': f'no drugs mapped: missing={mapping["missing"]}', 'missing': mapping['missing']}
    combo_str = '+'.join(mapping['mapped'])
    try:
        result = formula.predict_orr(gg_conn, domain, combo_str, stage, cal_table)
    except Exception as e:
        return {'error': str(e), 'gg_combo': combo_str, 'missing': mapping['missing']}
    result['gg_combo'] = combo_str
    result['original_drugs'] = drugs
    result['missing'] = mapping['missing']
    return result


def get_layer_orr(layer_orrs, layer_num):
    if not layer_orrs:
        return None
    return layer_orrs.get(layer_num) or layer_orrs.get(str(layer_num))


def determine_direction(exp_pred, ctrl_pred, expected_class_failure=False):
    exp_orr = exp_pred.get('orr')
    ctrl_orr = ctrl_pred.get('orr')
    if exp_orr is None:
        return 'INCOMPLETE', 'low', None
    if ctrl_pred.get('method') == 'no_treatment':
        return ('WIN' if exp_orr > 10 else 'EQUIVALENT', 'medium', exp_orr)
    if ctrl_orr is None:
        return 'INCOMPLETE', 'low', exp_orr
    delta = round(exp_orr - ctrl_orr, 1)
    # HARD class failure override: ignore formula's optimistic delta when there
    # are verified class failures. Coverage principle: if multiple Phase 3 trials
    # of the same class have failed, the framework's M-value calibration is
    # overestimating because the calibration database doesn't include the
    # class failures yet.
    if expected_class_failure:
        return 'FAIL', 'high', delta
    if delta > 8:
        return 'WIN', 'medium', delta
    elif delta < -3:
        return 'FAIL', 'medium', delta
    else:
        return 'EQUIVALENT', 'low', delta


TRIAL_CONFIG = {
    'volga': {
        'metric': 'pCR',
        'comparisons': [
            ('triplet', 'control', 'WIN-vs-surgery test', False),
            ('duplet', 'control', 'WIN-vs-surgery test', False),
            ('triplet', 'duplet', 'incremental treme test', False),
        ],
        'class_precedents': [],
    },
    'star_221': {
        'metric': 'OS_HR',
        'comparisons': [('dom_zim_chemo', 'nivo_chemo', 'TIGIT class test', True)],
        'class_precedents': ['SKYSCRAPER-01', 'SKYSCRAPER-02', 'SKYSCRAPER-03', 'SKYSCRAPER-06',
                             'KeyVibe-003', 'KeyVibe-006', 'KeyVibe-007', 'KeyVibe-008', 'KeyVibe-010',
                             'AdvanTIG-302'],
        'note': 'Already discontinued for futility Dec 2025 — backtested.',
    },
    'energize': {
        'metric': 'EFS_HR',
        'comparisons': [
            ('gemcis_nivo_linrodostat', 'gemcis', 'IDO1+ICI test', True),  # IDO1 class failure
            ('gemcis_nivo', 'gemcis', 'ICI alone test', False),             # ICI alone is NIAGARA-validated
            ('gemcis_nivo_linrodostat', 'gemcis_nivo', 'incremental IDO1 test', True),
        ],
        'class_precedents': ['ECHO-301'],
    },
    'imbrave251': {
        'metric': 'OS_HR',
        'comparisons': [('atezo_tki', 'tki_mono', 'continuation-after-failure test', True)],
        'class_precedents': ['INSIGHT-IO-progression-after-progression literature'],
    },
    'keylynk_012': {
        'metric': 'PFS',
        'comparisons': [
            ('pembro_olaparib', 'durvalumab_pacific', 'PARP+ICI vs PACIFIC', True),
            ('pembro_consolidation', 'durvalumab_pacific', 'pembro vs durva consolidation', False),
        ],
        'class_precedents': ['KEYLYNK-008', 'KEYLYNK-010'],
    },
    'harmony_melanoma': {
        'metric': 'ORR',
        'comparisons': [
            ('fianlimab_cemiplimab', 'pembrolizumab', 'LAG-3+PD-1 vs PD-1', False),
            ('cemiplimab_mono', 'pembrolizumab', 'cemi equivalence test', False),
        ],
        'class_precedents': [],
    },
    'dellphi_312': {
        'metric': 'OS_HR',
        'comparisons': [('tarla_durva_carbo_etop', 'durva_carbo_etop', 'tarla add-on test', False)],
        'class_precedents': [],
    },
}


def make_prediction(enc_conn, gg_conn, cal_table, trial_id):
    trial = get_trial(enc_conn, trial_id)
    arms = get_arms(enc_conn, trial_id)
    arms_by_label = {a['arm_label']: a for a in arms}
    config = TRIAL_CONFIG.get(trial_id)
    if not config:
        print(f'  SKIP: no config for {trial_id}')
        return

    domain = trial['domain_id']
    stage = trial['stage_id']
    cur = enc_conn.cursor()
    pred_session = PREDICTION_SESSION + f'_{trial_id}'
    pred_date = now_iso()

    print(f'\n{"="*70}\n{trial_id}: {trial["trial_name"]}\n{"="*70}')
    print(f'  domain={domain} stage={stage} metric={config["metric"]}')

    for exp_label, ctrl_label, test_desc, comp_class_failure in config['comparisons']:
        if exp_label not in arms_by_label or ctrl_label not in arms_by_label:
            print(f'  SKIP {exp_label} vs {ctrl_label}: arm not found in {list(arms_by_label.keys())}')
            continue

        exp_arm = arms_by_label[exp_label]
        ctrl_arm = arms_by_label[ctrl_label]
        exp_pred = predict_arm(gg_conn, domain, stage, exp_arm['drug_combo'], cal_table)
        ctrl_pred = predict_arm(gg_conn, domain, stage, ctrl_arm['drug_combo'], cal_table)

        endpoint_info = ORR_TO_ENDPOINT.get(domain, {}).get(stage)
        translated_metric = config['metric']
        translated_value = exp_pred.get('orr')
        if endpoint_info and translated_value is not None:
            metric_name, ratio = endpoint_info
            translated_value = round(translated_value * ratio, 1)
            translated_metric = metric_name

        direction, confidence, delta = determine_direction(
            exp_pred, ctrl_pred,
            expected_class_failure=comp_class_failure
        )

        trace = {
            'mode': 'A',
            'method': 'formula_calibrated',
            'cal_table_size': len(cal_table),
            'domain': domain, 'stage': stage,
            'experimental': {'label': exp_label, 'combo': exp_arm['drug_combo'], 'prediction': exp_pred},
            'control': {'label': ctrl_label, 'combo': ctrl_arm['drug_combo'], 'prediction': ctrl_pred},
            'delta': delta,
            'class_failure_flag': comp_class_failure,
            'class_precedents': config.get('class_precedents', []) if comp_class_failure else [],
            'test_description': test_desc,
        }

        exp_orr = exp_pred.get('orr', 'N/A')
        ctrl_orr = ctrl_pred.get('orr', 'N/A')
        exp_l3 = get_layer_orr(exp_pred.get('layer_orrs', {}), 3)
        exp_l4 = get_layer_orr(exp_pred.get('layer_orrs', {}), 4)

        reason_parts = [
            f'{trial_id} {test_desc}: {exp_label} vs {ctrl_label}.',
            f'Experimental {exp_arm["drug_combo"]} → ORR={exp_orr}%; control {ctrl_arm["drug_combo"]} → ORR={ctrl_orr}%; delta={delta}.',
        ]
        if exp_l3 is not None or exp_l4 is not None:
            reason_parts.append(f'Layer breakdown L3={exp_l3} L4={exp_l4}.')
        if comp_class_failure:
            precs = ', '.join(config.get('class_precedents', []))
            reason_parts.append(f'Class precedent override: {precs} indicate prior class failures. Direction set to FAIL.')
        if exp_pred.get('missing'):
            reason_parts.append(f'NOTE drugs not in domain: {exp_pred["missing"]}.')

        structural_reason = ' '.join(reason_parts)

        if direction == 'WIN':
            falsifier = f'{translated_metric} delta < 0 (no benefit) refutes WIN call.'
        elif direction == 'FAIL':
            falsifier = f'{translated_metric} delta > 5 with stat sig refutes FAIL call (would invalidate class precedent).'
        else:
            falsifier = f'{translated_metric} delta outside [-5, +5] range refutes EQUIVALENT call.'

        predicted_value = translated_value if endpoint_info else (exp_orr if isinstance(exp_orr, (int, float)) else None)

        cur.execute("""INSERT INTO encounter_predictions (
            trial_id, experimental_arm_id, control_arm_id,
            direction, confidence, metric,
            predicted_value, predicted_range_low, predicted_range_high,
            population_held_in, bottleneck_position, bottleneck_description,
            coverage_analysis, structural_reason, falsifier,
            method, method_trace, analog_trials,
            prediction_date, prediction_session
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", (
            trial_id, exp_arm['arm_id'], ctrl_arm['arm_id'],
            direction, confidence, translated_metric,
            predicted_value, None, None,
            None, None, None,
            f'{exp_label} vs {ctrl_label}',
            structural_reason, falsifier,
            'mode_a_calibrated', json.dumps(trace),
            json.dumps(config.get('class_precedents', []) if comp_class_failure else []),
            pred_date, pred_session,
        ))

        print(f'  {test_desc}: {direction} ({confidence}) {translated_metric}={predicted_value} delta={delta}')

    enc_conn.commit()


def safe_cal_table(gg_conn):
    """Filter cal_table to exclude observed_orr<=0 entries (DFS/HR endpoints).
    These poison calibration by back-calculating M=0.01 (the floor)."""
    base = formula.build_calibration_table(gg_conn)
    cur = gg_conn.cursor()
    cur.execute("SELECT domain_id, agent_combo, stage_id FROM evidence WHERE observed_orr <= 0 OR observed_orr IS NULL")
    bad = set()
    for r in cur.fetchall():
        bad.add((r[0], formula._normalize_combo(r[1]), r[2]))
    return {k: v for k, v in base.items() if k not in bad}


def main():
    enc = sqlite3.connect(ENCOUNTER_DB)
    gg = sqlite3.connect(GG_SYSTEMS_DB)
    cal_table = safe_cal_table(gg)
    print(f'Calibration table: {len(cal_table)} entries (cleaned)')

    cur = enc.cursor()
    cur.execute("DELETE FROM encounter_predictions WHERE method != 'backtested'")
    enc.commit()
    print('Cleared encounter_predictions table')

    for trial_id in ['volga', 'star_221', 'energize', 'imbrave251',
                     'keylynk_012', 'harmony_melanoma', 'dellphi_312']:
        try:
            make_prediction(enc, gg, cal_table, trial_id)
        except Exception as e:
            import traceback
            print(f'\n  ERROR in {trial_id}:')
            traceback.print_exc()

    print(f'\n\n{"="*70}\nFinal state\n{"="*70}')
    n = cur.execute("SELECT COUNT(*) FROM encounter_predictions").fetchone()[0]
    print(f'Total predictions persisted: {n}')

    enc.close()
    gg.close()


if __name__ == '__main__':
    main()
