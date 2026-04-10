"""add_sclc_domain.py — Add small-cell lung cancer (SCLC) as a new domain
in the GG framework work copy.

SCLC is a high-grade neuroendocrine cancer with rapid proliferation,
high mutational burden, but historically poor immunotherapy response
relative to NSCLC. The domain parameters are estimated from:
  - IMpower133 (atezo+chemo, 1L ES-SCLC) ORR ~60%, OS 12.3mo
  - CASPIAN (durva+chemo, 1L ES-SCLC) ORR ~67%, OS 13mo
  - DeLLphi-304 (tarlatamab 2L ES-SCLC) ORR ~32%, OS 13.6mo

Domain profile estimated from analogous parameters of NSCLC but with
higher dt (faster doubling) and slightly lower ICI baseline (cold tumor
relative to NSCLC).
"""
import sqlite3
import json
from pathlib import Path
# ─── Path resolution: locate sibling files relative to this script ───
import os as _os
_HERE = Path(_os.path.dirname(_os.path.abspath(__file__)))
_REPO = _HERE.parent
_DATA = _REPO / 'data'

from datetime import datetime

DB = _DATA / 'gg_systems_workcopy.db'


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # ── 1. Add domain ──
    cur.execute("""INSERT OR REPLACE INTO domains (id, name, type, description, created_at)
        VALUES (?, ?, ?, ?, ?)""",
        ('sclc', 'Small Cell Lung Cancer', 'cancer',
         'High-grade neuroendocrine pulmonary carcinoma. Extensive-stage SCLC = systemic disease at presentation. Standard 1L: chemo+IO induction (carboplatin+etoposide+atezo or durva). Historically poor response to ICI relative to NSCLC.',
         datetime.now().isoformat()))
    print('+ Added domain sclc')

    # ── 2. Add system_profile ──
    # dt (doubling time) lower than NSCLC reflects rapid SCLC proliferation
    # beta (T-cell exhaustion factor) slightly higher than NSCLC
    cur.execute("""INSERT OR REPLACE INTO system_profile (domain_id, dt, epsilon_sub, epsilon_top, beta, system_type)
        VALUES (?, ?, ?, ?, ?, ?)""",
        ('sclc', 35.0, 0.85, 0.65, 0.60, 'parallel'))
    print('+ Added system_profile (dt=35, beta=0.60)')

    # ── 3. Add system_states (stages) ──
    # Match NSCLC structure but most relevant for DeLLphi-312 is es_1l
    states = [
        ('ls_1l',  'sclc', 'Limited-stage 1L (cCRT)',  10, 'Limited 1L',     'Construction',  2, 1, 0, 1.0, 1),
        ('es_1l',  'sclc', 'Extensive-stage 1L',       14, 'ES-SCLC 1L',     'Conservation',  2, 6, 0, 1.0, 2),
        ('es_2l',  'sclc', 'Extensive-stage 2L+',      15, 'ES-SCLC 2L',     'Conservation',  2, 12, 1, 1.2, 3),
    ]
    for sid, dom, name, pos, sn, regime, depth, tau, prior_lines, gamma, sort_order in states:
        cur.execute("""INSERT OR REPLACE INTO system_state
            (id, domain_id, name, position, position_name, position_description, regime,
             depth, tau, prior_lines, gamma, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (sid, dom, name, pos, sn, name, regime, depth, tau, prior_lines, gamma, sort_order))
        print(f'+ Added stage {sid}: pos={pos} regime={regime} depth={depth}')

    # ── 4. Add agents ──
    # Core SCLC agents:
    # - Carboplatin / etoposide (chemo backbone, sp=1/2 cross/hold L=3)
    # - Atezolizumab / durvalumab (1L IO, sp=3 cross L=1)
    # - Topotecan / lurbinectedin / amrubicin (2L chemo, sp=2 hold L=3)
    # - Tarlatamab (DLL3 BiTE, NOVEL — sp=3 cross L=1, T-cell engager)
    agents = [
        ('carbo_s',   'sclc', 'Carboplatin',         1, 'cross', 0.45, 3, 'Platinum',
         'Cytotoxic platinum, sp=1 cross. Standard SCLC backbone.'),
        ('etop_s',    'sclc', 'Etoposide',           2, 'hold',  0.40, 3, 'Topoisomerase',
         'Topo-II inhibitor, sp=2 hold. Standard SCLC backbone with platinum.'),
        ('atezo_s',   'sclc', 'Atezolizumab',        3, 'cross', 0.32, 1, 'Checkpoint inhibitor',
         'Calibrated from IMpower133 ORR ~60% with chemo (M for atezo alone is small in SCLC, ~0.32).'),
        ('durva_s',   'sclc', 'Durvalumab',          3, 'cross', 0.34, 1, 'Checkpoint inhibitor',
         'Calibrated from CASPIAN ORR ~67% with chemo. Slightly higher than atezo per CASPIAN.'),
        ('topo_s',    'sclc', 'Topotecan',           2, 'hold',  0.18, 3, 'Topoisomerase',
         '2L SCLC chemo. ORR ~16% historic. Conservative M.'),
        ('lurbi_s',   'sclc', 'Lurbinectedin',       2, 'hold',  0.22, 3, 'Alkylating',
         '2L SCLC ORR ~22% (Trigo 2020). Conservative M.'),
        ('tarla_s',   'sclc', 'Tarlatamab',          3, 'cross', 0.55, 1, 'Bispecific T-cell engager',
         'DeLLphi-304 2L mono ORR ~32%, OS HR 0.60 vs chemo. M=0.55 reflects strong 2L signal.'
         ' Novel mechanism: DLL3 BiTE engages CD3+ T cells against DLL3+ SCLC cells.'
         ' Same sub-phase as anti-PD-1 (effector engagement) but mechanism is direct rather than de-inhibition.'),
    ]
    for aid, dom, name, sp, op, M, L, cls, notes in agents:
        cur.execute("""INSERT OR REPLACE INTO agents
            (id, domain_id, name, subphase, function, M, action, subposition, mechanism, class,
             calibration_quality, calibration_source, calibration_confidence, calibration_basis,
             approved, year_approved, biomarker, notes, operation, mechanism_depth)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (aid, dom, name, sp, 'effector', M, 'release_brake', None, cls, cls,
             'estimated', notes, 1, notes, 1, 2025, None, notes, op, L))
        print(f'+ Added agent {aid}: {name} sp={sp} op={op} M={M} L={L}')

    conn.commit()

    # ── Calibration evidence ──
    # IMpower133, CASPIAN, DeLLphi-304, topotecan baseline.
    # These rows feed formula.build_calibration_table() so predict_orr returns
    # observed-anchored values for sclc instead of saturating to 0.
    sclc_evidence = [
        ('atezo_s+carbo_s+etop_s', 'es_1l', 'IMpower133', 60.2, 403, 2018,
         'Horn NEJM 2018', 'ORR', 'IMpower133 1L ES-SCLC: atezo+carbo+etop'),
        ('durva_s+carbo_s+etop_s', 'es_1l', 'CASPIAN', 68.0, 537, 2019,
         'Paz-Ares Lancet 2019', 'ORR', 'CASPIAN 1L ES-SCLC: durva+platinum+etop'),
        ('tarla_s', 'es_2l', 'DeLLphi-304', 40.0, 254, 2025,
         'Mountzios NEJM 2025', 'ORR', 'DeLLphi-304 2L SCLC tarla mono; HR OS 0.60; FDA full approval Nov 2025'),
        ('topo_s', 'es_2l', 'Topotecan baseline', 20.0, 100, 2007,
         "O'Brien JCO 2006", 'ORR', 'Standard 2L SCLC topotecan ORR ~15-25%'),
    ]
    for combo, stage_id, trial_name, orr, n, year, source, endpoint, notes in sclc_evidence:
        cur.execute("""INSERT OR REPLACE INTO evidence
            (domain_id, agent_combo, stage_id, trial_name, observed_orr, n, year, source, endpoint, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            ('sclc', combo, stage_id, trial_name, orr, n, year, source, endpoint, notes))
        print(f'+ Added evidence {trial_name}: {combo} ORR={orr}%')

    # Calibrate dt to give max_orr ~70% at depth=2
    # rd = 60/(60+dt) * (1 - 1/depth); for depth=2 and target rd=0.30: dt=40
    cur.execute("UPDATE system_profile SET dt=40 WHERE domain_id='sclc'")
    print('+ Updated SCLC dt=40 (max_orr ~70% at depth=2)')

    conn.commit()

    # Verify
    n_states = cur.execute("SELECT COUNT(*) FROM system_state WHERE domain_id='sclc'").fetchone()[0]
    n_agents = cur.execute("SELECT COUNT(*) FROM agents WHERE domain_id='sclc'").fetchone()[0]
    print(f'\nSCLC domain ready: {n_states} stages, {n_agents} agents')
    conn.close()


if __name__ == '__main__':
    main()
