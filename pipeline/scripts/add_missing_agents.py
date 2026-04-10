"""add_missing_agents.py — Add agents required for the remaining 5 trials
to the GG framework work copy. All M values are estimated from class
analogs in the same domain when possible.

Each agent gets calibration_quality='estimated' and a clear note about
the analog used. None of these are calibrated against the agent's own
historical observed ORR — when those readouts exist (e.g. KEYLYNK-008
for olaparib+pembro), they should later be added to the evidence table.
"""
import sqlite3
from pathlib import Path
# ─── Path resolution: locate sibling files relative to this script ───
import os as _os
_HERE = Path(_os.path.dirname(_os.path.abspath(__file__)))
_REPO = _HERE.parent
_DATA = _REPO / 'data'


DB = _DATA / 'gg_systems_workcopy.db'

# Each tuple: (id, domain, name, sp, op, M, L, mechanism, class, source)
NEW_AGENTS = [
    # ── VOLGA: urothelial durvalumab + tremelimumab ──
    ('durva',     'urothelial', 'Durvalumab',   3, 'cross', 0.58, 1,
     'anti-PD-L1', 'Checkpoint inhibitor',
     '2026-04-10: estimated from urothelial pembro_bl (M=0.678) and NSCLC durva (M=0.58); same anti-PD-(L)1 class. Used the lower NSCLC value as conservative anchor for VOLGA prediction.'),
    ('treme',     'urothelial', 'Tremelimumab', 1, 'cross', 0.56, 1,
     'anti-CTLA-4', 'Checkpoint inhibitor',
     '2026-04-10: estimated from POSEIDON NSCLC treme (M=0.56). CTLA-4 priming is sp=1 cross (Catalyst). Adds Construction sub-phase coverage to durvalumab effector for VOLGA triplet.'),

    # ── STAR-221: gastric domain ──
    ('domv_ga',   'gastric', 'Domvanalimab',    1, 'cross', 0.55, 1,
     'anti-TIGIT', 'Checkpoint inhibitor',
     '2026-04-10: estimated from POSEIDON treme M=0.56; TIGIT class is sp=1 priming like CTLA-4. Note: TIGIT class has 11 verified Ph3 failures across multiple sponsors — add as agent for prediction but expect novel coverage to fail.'),
    ('zimb_ga',   'gastric', 'Zimberelimab',    3, 'cross', 0.27, 1,
     'anti-PD-1', 'Checkpoint inhibitor',
     '2026-04-10: estimated from gastric nivo_ga M=0.27; same class (anti-PD-1), same domain calibration anchor.'),

    # ── ENERGIZE: urothelial nivolumab + linrodostat ──
    ('nivo_bl',   'urothelial', 'Nivolumab',    3, 'cross', 0.65, 1,
     'anti-PD-1', 'Checkpoint inhibitor',
     '2026-04-10: estimated from urothelial pembro_bl M=0.678; same class anti-PD-(L)1, slightly conservative.'),
    ('linro_bl',  'urothelial', 'Linrodostat',  2, 'hold', 0.30, 1,
     'IDO1 inhibitor', 'Targeted therapy',
     '2026-04-10: estimated from ECHO-301 epacadostat null result. IDO1 class added no benefit to PD-1 in melanoma. M conservatively low (0.30) reflects historical class failure. sp=2 hold is metabolic enzyme blocking.'),

    # ── IMbrave251: hcc lenvatinib already exists as lenva_h ──
    # nothing to add

    # ── KEYLYNK-012: nsclc olaparib ──
    ('ola_l',     'nsclc', 'Olaparib',          2, 'hold', 0.32, 2,
     'PARP inhibitor', 'Targeted therapy',
     '2026-04-10: estimated from KEYLYNK-008 (NSCLC pembro+olaparib failed) and KEYLYNK-010 (mCRPC failed). Both class precedents indicate olaparib adds minimal in PD-1+ settings without HRD selection. Conservative M=0.32 reflects two class failures.'),

    # ── Harmony Melanoma: cemiplimab + fianlimab ──
    ('cemi_m',    'melanoma', 'Cemiplimab',     3, 'cross', 0.621, 1,
     'anti-PD-1', 'Checkpoint inhibitor',
     '2026-04-10: estimated from melanoma pembro_m M=0.621; same class (anti-PD-1), no head-to-head data favoring either; conservative match.'),
    ('fian_m',    'melanoma', 'Fianlimab',      4, 'cross', 0.65, 1,
     'anti-LAG-3', 'Checkpoint inhibitor',
     '2026-04-10: estimated from RELATIVITY-047 relatlimab analog. Phase 1 fianlimab+cemi showed 57% ORR in n=98 anti-PD-1 naive melanoma. M=0.65 reflects stronger Phase 1 signal than relatlimab Phase 3. NOTE: fianlimab is L4 (genomic) per get_agent_layer but actually structural — manually placed sp=4 cross because LAG-3 is a Conservation cross like relatlimab not Construction. Confirm with Raimo.'),
    ('rela_m',    'melanoma', 'Relatlimab',     4, 'cross', 0.605, 1,
     'anti-LAG-3', 'Checkpoint inhibitor',
     '2026-04-10: calibrated from RELATIVITY-047 ORR 43.9% (n=355). M back-calculated assuming nivo M=0.641 baseline + 10pp incremental → effective M_combo for nivo+rela. Direct rela M extracted via Bliss decomposition.'),
]


def add_agent(cur, agent_id, domain, name, sp, op, M, L, mech, cls, source_note):
    cur.execute("""INSERT OR REPLACE INTO agents
        (id, domain_id, name, subphase, function, M, action, subposition, mechanism, class,
         calibration_quality, calibration_source, calibration_confidence, calibration_basis,
         approved, year_approved, biomarker, notes, operation, mechanism_depth)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (agent_id, domain, name, sp, 'effector', M, 'release_brake', None,
         mech, cls, 'estimated', source_note, 1, source_note, 1, 2025, None,
         f'Added 2026-04-10 for encounter pipeline. {source_note}', op, L))


def main():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    print(f'Adding {len(NEW_AGENTS)} new agents to GG work copy...')
    for tup in NEW_AGENTS:
        add_agent(cur, *tup)
        print(f'  + {tup[1]:12s} {tup[0]:12s} {tup[2]:25s} sp={tup[3]} op={tup[4]} M={tup[5]} L={tup[6]}')
    conn.commit()

    # Verify each domain
    print('\nVerification — agents per domain after additions:')
    for domain in ['urothelial', 'gastric', 'melanoma', 'nsclc', 'hcc']:
        cur.execute("SELECT COUNT(*) FROM agents WHERE domain_id=?", (domain,))
        n = cur.fetchone()[0]
        print(f'  {domain}: {n}')
    conn.close()


if __name__ == '__main__':
    main()
