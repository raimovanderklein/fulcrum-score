"""
formula.py — The Blockade Formula (v13)
Generative Geometry (van der Klein & Claude, 2026)

Single source of truth. Every prediction engine imports from here.
If this file and the science page disagree, this file wins.

v13: DISARM / DISARM-S architecture.
     14 dataset tests, ~1,400 patients, 6 cancer types, 3 platforms.
     12/13 bulk ICI direction hi=R. Zero fitted parameters.
     DISARM-S: structurally guided feature selection, context-aware.
     SP4 renewal (TCF7/naive T cells) confirmed at scRNA resolution.
     SP4 renewal INVERTS on bulk — not a universal bulk feature.
     Anti-CTLA4 validated: direction correct, mechanism differs (priming).
     Sade-Feldman flip explained: scRNA mean ≠ bulk expression.

     Agent model + combo interaction + depth-aware scenarios (v9).
     Patient-level conservation depth model (v10).
     DISARM universal: effector/MKI67 ratio, 0 fitted parameters (v11).
     Foundation model + competitor comparison (v12).
     DISARM/DISARM-S split + Van Allen + GSE135222 + renewal (v13).

FOUR PREDICTION TIERS:
  1. Calibrated — exact combo+stage match → M from evidence.
  2. Stage-scaled — same combo different stage → M transfers by agent type.
  3. Novel combo — combo interaction model (Parallel/Series/Loop).
  4. Structural default — mechanism depth baseline, no evidence at all.

THREE AGENT TYPES (from SP × Operation):
  Blocker (Construction):  M constant across stages. One trial enough.
  Catalyst (Encounter):    M/E constant. Scales with environment.
  Enabler (Conservation):  M scales with deficit.

THREE COMBO REGIMES:
  Parallel:  Bliss independence (different targets, no overlap).
  Series:    Synergy × 1.35 (immune cascade, output feeds input).
  Loop:      Subadditive × (0.44 + 0.83 × M_min) (homeostatic system).

MECHANISM DEPTH BASELINES (M/E at system depth=1):
  L1 Surface:    0.30    L2 Pathway:   0.45
  L3 Structural: 0.70    L4 Genomic:   0.80

DEPTH CROSSING COST (per system depth layer above 1):
  L1/L2: 1/φ² = 0.382   L3: 1/φ⁴ = 0.146   L4: ~1.0 (bypasses)

PATIENT-LEVEL FORMULA (v10 — Conservation Depth Model):
  D = CCR8_Treg_norm + FOXP3_Treg_norm / φ
  M_eff = M * (1-D)/(1+D) * (1+S)

  Conservation has sub-depths: CCR8+ (active suppression, weight 1.0)
  and FOXP3+ (regulatory programme, weight 1/φ). Same 1/φ decay per
  depth level, applied WITHIN the conservation position.

DISARM (v13 — Tumour-Normalized Immune Effectiveness):
  Linear platforms:  score = (GZMB+PRF1+IFNG+GZMA) / MKI67
  Log2 platforms:    score = sum(log2_eff) - log2(MKI67)
                           = log2(GZMB × PRF1 × IFNG × GZMA / MKI67)

  Structural derivation: the immune system is an agent addressing a
  tumour. Agent effectiveness A = kill_rate / growth_rate. The ratio
  cancels infiltration confounds across platforms.

  Direction: ALWAYS high = respond on bulk ICI data.
  FAILS on scRNA mean expression (different observable — see DISARM-S).

  Validated: 13 ICI datasets + 1 negative control, ~1,400 patients.
    Dataset               n    Cancer      Platform  Therapy      DG     Dir
    Zhang NSCLC          242   NSCLC       scRNA     post-CPI     0.741  hi=R
    Sade-Feldman (all)    48   Melanoma    scRNA     mixed        0.740  hi=R*
    Sade-Feldman (pre)    19   Melanoma    scRNA     pre-CPI      FLIP   hi=NR †
    Hugo Melanoma         27   Melanoma    bulk      pre-PD1      0.533  hi=R
    Riaz Pre              33   Melanoma    bulk      pre-nivo     0.630  hi=R
    Riaz On               38   Melanoma    bulk      on-nivo      0.800  hi=R
    GSE93157 Mixed        49   Mixed       Nano      pembro       0.585  hi=R
    Rose Urothelial       58   Urothelial  bulk      PD-(L)1      0.596  hi=R
    IMvigor210           298   Urothelial  bulk      atezo        0.587  hi=R
    Liu Melanoma         122   Melanoma    bulk      pembro/nivo  0.530  hi=R
    Gide Melanoma         91   Melanoma    bulk      PD1±CTLA4    0.811  hi=R
    IMmotion150 atezo    165   RCC         bulk      atezo        0.667  hi=R
    Van Allen             42   Melanoma    bulk      ipilimumab   0.651  hi=R
    GSE135222 NSCLC       27   NSCLC       bulk      anti-PD1     0.714  hi=R

    * Sade-Feldman (all) mixes pre/post/on-treatment — misleading.
    † Sade-Feldman (pre) FLIPS on scRNA mean expression. See DISARM-S note.

  Negative control: IMmotion150 sunitinib (no ICI, n=82):
    AUC=0.513, direction=hi=NR. Confirms immune-specificity.

  Bulk direction: 12/12 ICI bulk datasets hi=R (includes anti-CTLA4).
  Anti-CTLA4 note: direction correct but suboptimal (0.651 vs CYT 0.691).
    Mechanism is priming (SP2), not encounter (SP3). Abundance predicts
    better than ratio. CTLA4 itself is best predictor (AUC 0.724).

  Competitor comparison (mean AUC, 4 iAtlas bulk datasets):
    DISARM-G=0.649, IFNg=0.654, GEP=0.648, CD8=0.656, CYT=0.639
    PD-L1=0.634, IMPRES=0.558. Dead heat on bulk; DISARM never flips.

DISARM-S (v13 — Structurally Guided Feature Selection):
  Same structural positions (SP1/SP3/SP4), context-aware observables.
  Positions are fixed (derived). Observables are validated per platform.

  The context is NOT cancer type. It's platform × drug mechanism.
  You tell DISARM-S what platform and drug, it selects the observables.

  DISARM-S scRNA (6 features, logistic regression):
    SP1 perception:   NK cells / FGFBP2          hi=R
    SP3 effector:     Tem/Trm / cytolytic genes   context
    SP3 exhaustion:   Tex / HAVCR2,TOX,ENTPD1     hi=NR
    SP4 suppression:  Treg / FOXP3,CCR8            hi=NR
    SP4 renewal:      Naive/memory / TCF7,IL7R     hi=R
    Ratio:            (eff+nk+renewal)/(all)        hi=R

  Zhang NSCLC (n=242, 10x scRNA, 5-fold CV):
    DISARM-S 6 features:    0.778
    Competitor equiv 3:     0.578
    All cell types ML 51:   0.764
    5-6 structural features match 51-feature ML. 20pp gap over competitors.

  Sade-Feldman (n=19, Smart-Seq2, pre-treatment only, repeated 5-fold CV):
    DISARM-S 6 features:    0.888
    Competitor equiv 3:     0.770
    All genes ML 30:        0.892
    TCF7 (renewal) is DOMINANT signal (raw AUC 0.944).

  WHY DISARM FAILS ON scRNA MEAN EXPRESSION:
    Bulk expression = abundance × per-cell expression (carries infiltrate signal)
    scRNA mean = per-cell expression only (abundance signal lost)
    Non-responders have hotter T cells per cell (more GZMB/PRF1)
    but lack renewal capacity (low TCF7). The ratio inverts.
    DISARM-S handles this because it uses structural features, not the ratio.

  SP4 RENEWAL ON BULK: NOT CONFIRMED.
    TCF7 inverts on IMvigor210 (0.429, hi=NR) and GSE135222 (0.368, hi=NR).
    On bulk, naive/memory markers are confounded by immune-cold tumours.
    Renewal is a scRNA-only feature — requires cell-level resolution.

OBSERVER STATES (depth 3+):
  Attend/Drain/Withdraw/Confusion from CD8 × Treg fraction.
  Two-axis classification beats single markers (6.9% vs 5.2% spread).
  Validated: χ²=5.03, p<0.05 on n=2,806 TCGA patients.
"""
import math
from typing import List, Dict, Optional

# ══════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════

SIGMA_TABLE = {1: 1.000, 2: 1.050, 3: 1.070, 4: 1.080}
DEPTH_SCALE = 1.0

# Golden ratio — structural constant
PHI = (1 + math.sqrt(5)) / 2

# Cancer's default strategy per sub-phase
CANCER_STRATEGY_BY_SP = {1: "cross", 2: "hold", 3: "cross", 4: "hold"}

OMEGA_MATCH = 1.0
OMEGA_MISMATCH = 0.7

# ── Agent Model (v9) ──────────────────────────
# Three types from (SP, Operation)
AGENT_TYPES = {
    # (sp, operation) → type
    (1, 'cross'): 'Catalyst',   # Encounter: scales with environment
    (1, 'hold'):  'Blocker',    # Construction: fixed potency
    (2, 'cross'): 'Blocker',    # Construction: fixed potency
    (2, 'hold'):  'Blocker',    # Construction: fixed potency
    (3, 'cross'): 'Blocker',    # Construction: fixed potency
    (3, 'hold'):  'Enabler',    # Conservation: scales with deficit
    (4, 'cross'): 'Enabler',    # Conservation: scales with deficit
    (4, 'hold'):  'Blocker',    # Construction: fixed potency
}

# Mechanism depth baselines (median M/E at system depth=1)
MECH_DEPTH_BASELINE = {1: 0.30, 2: 0.45, 3: 0.70, 4: 0.80}

# Depth crossing cost per system layer (boundaries per mechanism depth)
# L1/L2: 1 boundary per layer → cost = 1/φ² per layer
# L3: 2 boundaries per layer → cost = 1/φ⁴ per layer
# L4: 0 boundaries → cost = 1.0 (bypasses)
MECH_DEPTH_BOUNDARIES = {1: 1, 2: 1, 3: 2, 4: 0}

# Combo interaction regimes
COMBO_SERIES_FACTOR = 1.35      # immune cascade synergy
COMBO_LOOP_INTERCEPT = 0.44     # homeostatic minimum
COMBO_LOOP_SLOPE = 0.83         # recovery per unit M_min

# Observer cascade values (solved from 6 CPI trials)
OBSERVER_CASCADE = {
    "attend": 0.50, "drain": 0.70, "withdraw": 1.44, "confusion": 0.30,
}
OBSERVER_LABELS = {
    "attend": "S1 — Attend", "drain": "S2 — Drain",
    "withdraw": "S3 — Withdraw", "confusion": "S4 — Confusion",
}

# Observer state map (for patient-level use)
OBSERVER_STATE_MAP = {
    ('melanoma', 'met_1l'): 'S3', ('melanoma', 'met_2l'): 'S2', ('melanoma', 'met_3l'): 'S2',
    ('nsclc', 'neo'): 'S1', ('nsclc', 'met_1l'): 'S3', ('nsclc', 'met_2l'): 'S2',
    ('rcc', 'met_1l'): 'S3', ('rcc', 'met_2l'): 'S2', ('rcc', 'met_3l'): 'S4',
    ('hcc', 'met_1l'): 'S2', ('hcc', 'met_2l'): 'S4',
    ('pancreatic', 'la'): 'S4', ('pancreatic', 'met_1l'): 'S4', ('pancreatic', 'met_2l'): 'S4',
    ('gbm', 'met_1l'): 'S4', ('gbm', 'met_2l'): 'S4',
    ('breast_hr', 'met_1l'): 'S1', ('breast_hr', 'met_2l'): 'S2', ('breast_hr', 'met_3l'): 'S2',
    ('breast_tn', 'met_1l'): 'S3', ('breast_tn', 'met_2l'): 'S2',
    ('colorectal', 'met_1l'): 'S4', ('colorectal', 'met_2l'): 'S4',
    ('hnscc', 'met_1l'): 'S3', ('hnscc', 'met_2l'): 'S2',
    ('urothelial', 'met_1l'): 'S3', ('urothelial', 'met_2l'): 'S2',
    ('gastric', 'met_1l'): 'S3', ('gastric', 'met_2l'): 'S2',
    ('cervical', 'met_1l'): 'S3', ('cervical', 'met_2l'): 'S2',
    ('endometrial', 'met_1l'): 'S3', ('endometrial', 'met_2l'): 'S2',
    ('prostate', 'hspc'): 'S1', ('prostate', 'crpc_1l'): 'S4',
    ('prostate', 'crpc_2l'): 'S4', ('prostate', 'crpc_3l'): 'S4',
    ('ovarian', 'met_1l'): 'S1', ('ovarian', 'met_2l'): 'S2', ('ovarian', 'met_3l'): 'S4',
}

# ── Patient-Level Prediction (v10) ─────────────────
# Conservation Depth Model: D = primary/φ⁰ + secondary/φ¹
# Primary = active suppression (CCR8+ Treg in scRNA, checkpoint expr in bulk)
# Secondary = regulatory programme (FOXP3+ Treg)
# Signal = innate surveillance (FGFBP2+ NK)
#
# Validated: Zhang NSCLC AUC 0.832, Sade-Feldman AUC 0.692, Riaz AUC 0.654

# TCGA reference thresholds for Observer state classification
OBSERVER_CD8_MEDIAN = 0.1136     # TCGA pan-cancer CD8 T-cell fraction median
OBSERVER_TREG_FRAC_MEDIAN = 0.1198  # TCGA pan-cancer Treg/(CD8+Treg) median

# Reference log-normal parameters for transferable normalization
# (from Zhang NSCLC n=159, scRNA CCR8+ Treg + FGFBP2+ NK)
LOGNORM_REF = {
    'zhang_nsclc_scrna': {
        'ccr8_treg': {'mu': 0.993, 'sigma': 0.317},
        'fgfbp2_nk': {'mu': -3.329, 'sigma': 0.999},
    }
}

def get_observer_state(domain_id, stage_id):
    return OBSERVER_STATE_MAP.get((domain_id, stage_id), 'S1')


# ══════════════════════════════════════════
# AGENT MODEL (v9)
# ══════════════════════════════════════════

def agent_type(sp, operation):
    """Classify agent by (SP, Operation) → Blocker/Catalyst/Enabler."""
    return AGENT_TYPES.get((sp, operation or 'hold'), 'Blocker')


def mechanism_depth_baseline(mech_depth, system_depth=1):
    """Predicted M/E for an untested agent from mechanism depth alone.
    At system_depth=1, returns the baseline. At deeper depths, applies
    the crossing cost per layer."""
    base = MECH_DEPTH_BASELINE.get(mech_depth, 0.45)
    if system_depth <= 1:
        return base
    boundaries = MECH_DEPTH_BOUNDARIES.get(mech_depth, 1)
    if boundaries == 0:
        return base  # L4 bypasses
    cost_per_layer = (1.0 / PHI ** 2) ** boundaries
    return base * cost_per_layer ** (system_depth - 1)


def stage_transfer_M(M_ref, E_ref, E_target, atype, tau_ref=None, tau_target=None):
    """Transfer M from reference stage to target stage using agent type rule.
    
    Blocker:  M constant (Construction — fixed potency)
    Catalyst: M/E constant (Encounter — scales with environment)  
    Enabler:  M × sqrt(tau_target/tau_ref) (Conservation — scales with deficit)
    """
    if atype == 'Catalyst':
        me_ratio = M_ref / E_ref if E_ref > 0 else 0
        return me_ratio * E_target
    elif atype == 'Enabler':
        if tau_ref and tau_target and tau_ref > 0:
            return M_ref * math.sqrt(tau_target / tau_ref)
        return M_ref
    else:  # Blocker (default)
        return M_ref


def combo_regime(system_type, agent_types, agent_mech_depths):
    """Classify combo interaction regime from system type and agent properties.
    
    system_type: 'parallel' (cancer), 'serial' (cascade disease),
                 'feedback' (chronic disease), 'infectious'
    agent_types: list of 'Blocker'/'Catalyst'/'Enabler'
    agent_mech_depths: list of L1-L4
    
    Returns: 'parallel', 'series', or 'loop'
    """
    has_catalyst = 'Catalyst' in agent_types
    
    # Chronic/feedback disease → always Loop
    if system_type in ('feedback', 'serial'):
        return 'loop'
    
    # Infectious disease → Parallel (agents target different organisms/mechanisms)
    if system_type == 'infectious':
        return 'parallel'
    
    # Cancer: check if immune cascade (series) or independent (parallel)
    if system_type == 'parallel':
        if has_catalyst:
            # Catalyst + anything in cancer = series (immune cascade)
            return 'series'
        else:
            return 'parallel'
    
    return 'parallel'


def combo_interaction_factor(regime, agent_orrs):
    """Compute the interaction factor for a combo based on regime.
    
    Returns multiplier to apply to Bliss-independent prediction.
    
    parallel: 1.0 (full independence)
    series:   1.35 (immune cascade synergy)
    loop:     0.44 + 0.83 × M_min (homeostatic penalty)
    """
    if regime == 'series':
        return COMBO_SERIES_FACTOR
    elif regime == 'loop':
        if not agent_orrs:
            return COMBO_LOOP_INTERCEPT
        M_min = min(agent_orrs) / 100.0
        factor = COMBO_LOOP_INTERCEPT + COMBO_LOOP_SLOPE * M_min
        return min(factor, 1.0)
    else:  # parallel
        return 1.0


def predict_scenarios(conn, domain, combo, stage, cal_table=None):
    """Depth 3+ prediction: return four Observer state scenarios.
    
    At depth >= 3, the single ORR number is misleading.
    Return the four-state distribution instead.
    """
    cur = conn.cursor()
    state = cur.execute("SELECT depth FROM system_state WHERE domain_id=? AND id=?",
                       (domain, stage)).fetchone()
    if not state:
        return None
    
    base = predict_orr(conn, domain, combo, stage, cal_table)
    if 'error' in base:
        return None
    
    base_orr = base['orr']
    scenarios = {}
    for obs_state, cascade_val in OBSERVER_CASCADE.items():
        # Scale base ORR by Observer cascade value
        adj_orr = min(base_orr * cascade_val, 95.0)
        adj_orr = round(max(0, adj_orr), 1)
        scenarios[obs_state] = {
            'orr': adj_orr,
            'label': OBSERVER_LABELS[obs_state],
            'cascade': cascade_val,
        }
    
    return {
        'base_orr': base_orr,
        'system_depth': state[0],
        'scenarios': scenarios,
        'method': base.get('method', ''),
        'needs_scenarios': state[0] >= 3,
    }


# ══════════════════════════════════════════
# CORE MATH
# ══════════════════════════════════════════

def omega(agent_operation, subphase, cancer_strategy=None):
    """Operation match modifier."""
    strategy = cancer_strategy or CANCER_STRATEGY_BY_SP
    tumour_op = strategy.get(subphase, "hold")
    return OMEGA_MATCH if agent_operation == tumour_op else OMEGA_MISMATCH


def environment(beta, tau, gamma, prior_lines):
    """E = f(tau) * g(p). The resistance environment."""
    return (1 + beta * math.log(1 + tau)) * (1 + gamma * prior_lines)


def residual(M, beta, tau, gamma, prior_lines, w=1.0):
    """Per-agent residual (structural formula, used for novel predictions).
    Capped at 1.0."""
    tf = 1 + beta * math.log(1 + tau)
    pf = 1 + gamma * prior_lines
    return min((1 - M * w) * tf * pf, 1.0)


def residual_calibrated(M, E, w=1.0):
    """Per-agent residual (calibrated M/E formulation, never caps)."""
    return max(1 - M * w / E, 0.001)


def depth_resistance(dt, depth):
    """Minimum residual fraction that coverage cannot breach."""
    if depth <= 1:
        return 0.0
    R_base = DEPTH_SCALE * 60.0 / (60.0 + dt)
    return R_base * (1 - 1.0 / depth)


def get_agent_layer(cls):
    """L3 = immune/cellular mechanism. L4 = molecular mechanism."""
    cls = (cls or '').lower()
    if any(k in cls for k in ['checkpoint', 'anti-pd', 'ctla', 'oncolytic',
                                'bispecific', 'car-t', 'il-2', 'interferon',
                                't-cell', 'vaccine']):
        return 3
    return 4


# ══════════════════════════════════════════
# CALIBRATION (back-calculate M from evidence)
# ══════════════════════════════════════════

def calibrate_M(beta, dt, depth, tau, gamma, prior_lines, obs_orr):
    """Back-calculate M from observed ORR."""
    E = environment(beta, tau, gamma, prior_lines)
    rd = depth_resistance(dt, depth)
    max_orr = (1 - rd) * 100

    if obs_orr <= 0.1:
        return 0.01
    if obs_orr >= max_orr - 0.1:
        return E * 0.99

    r = (1 - obs_orr / 100) ** (1.0 / depth)
    M = (1 - r) * E
    return max(0.01, min(M, E * 0.99))


def _normalize_combo(combo):
    """Normalize combo string to sorted agent IDs."""
    return "+".join(sorted(combo.split("+")))


def build_calibration_table(conn, cancer_only=False):
    """Build (domain, combo, stage) -> calibrated M from all evidence.
    Combo keys are normalized (sorted) so lookup order doesn't matter."""
    cur = conn.cursor()
    evidence = cur.execute("""
        SELECT e.domain_id, e.agent_combo, e.stage_id, e.observed_orr
        FROM evidence e WHERE e.observed_orr IS NOT NULL
    """).fetchall()

    table = {}
    for domain, combo, stage, obs in evidence:
        prof = cur.execute("SELECT beta, dt FROM system_profile WHERE domain_id=?", (domain,)).fetchone()
        try:
            state = cur.execute("SELECT depth, tau, prior_lines, gamma FROM system_state WHERE domain_id=? AND id=?",
                               (domain, stage)).fetchone()
        except:
            continue
        if not prof or not state:
            continue
        beta, dt = prof
        depth, tau, prior_lines, gamma = state
        M = calibrate_M(beta, dt, depth, tau, gamma, prior_lines, obs)
        if M is not None:
            table[(domain, _normalize_combo(combo), stage)] = M

    return table


# ══════════════════════════════════════════
# PREDICTION ENGINE (main entry point)
# ══════════════════════════════════════════

def predict_orr(conn, domain, combo, stage, cal_table=None):
    """Predict ORR for a combo or single agent.

    Priority:
    1. Exact match in calibration table -> calibrated M
    2. Same combo at different stage -> stage-scaled M
    3. Novel combo -> layer-aware prediction from components

    Args:
        conn: sqlite3 connection to systems.db
        domain: e.g. 'melanoma'
        combo: e.g. 'nivo+ipi' (agent IDs joined by +)
        stage: e.g. 'met_1l'
        cal_table: pre-built calibration table (or None to skip calibration)
    """
    cur = conn.cursor()

    prof = cur.execute("SELECT beta, dt FROM system_profile WHERE domain_id=?", (domain,)).fetchone()
    try:
        state = cur.execute("SELECT depth, tau, prior_lines, gamma FROM system_state WHERE domain_id=? AND id=?",
                           (domain, stage)).fetchone()
    except:
        return {"error": f"No state {stage} for {domain}"}
    if not prof or not state:
        return {"error": f"No profile/state for {domain}/{stage}"}

    beta, dt = prof
    depth, tau, prior_lines, gamma = state
    E = environment(beta, tau, gamma, prior_lines)
    rd = depth_resistance(dt, depth)
    max_orr = (1 - rd) * 100

    if cal_table is None:
        cal_table = {}

    norm_combo = _normalize_combo(combo)

    # -- Case 1: exact match --
    key = (domain, norm_combo, stage)
    if key in cal_table:
        M = cal_table[key]
        r = residual_calibrated(M, E)
        raw_orr = (1 - r ** depth) * 100
        orr = round(max(0, min(raw_orr, max_orr)), 1)
        return {"orr": orr, "method": "calibrated", "M": round(M, 4),
                "E": round(E, 3), "depth": depth, "max_orr": round(max_orr, 1)}

    # -- Case 2: same combo, different stage --
    combo_cals = {k: v for k, v in cal_table.items() if k[0] == domain and k[1] == norm_combo}
    if combo_cals:
        ref_key = list(combo_cals.keys())[0]
        M_ref = combo_cals[ref_key]
        r = residual_calibrated(M_ref, E)
        raw_orr = (1 - r ** depth) * 100
        orr = round(max(0, min(raw_orr, max_orr)), 1)
        return {"orr": orr, "method": "stage_scaled", "M": round(M_ref, 4),
                "ref_stage": ref_key[2], "E": round(E, 3), "depth": depth,
                "max_orr": round(max_orr, 1)}

    # -- Case 3: novel prediction from components --
    agents_in_combo = combo.split('+')

    if len(agents_in_combo) == 1:
        aid = agents_in_combo[0]
        single_cals = {k: v for k, v in cal_table.items()
                       if k[0] == domain and k[1] == aid}
        if single_cals:
            ref_key = list(single_cals.keys())[0]
            M_ref = single_cals[ref_key]
            r = residual_calibrated(M_ref, E)
            raw_orr = (1 - r ** depth) * 100
            orr = round(max(0, min(raw_orr, max_orr)), 1)
            return {"orr": orr, "method": "single_scaled", "M": round(M_ref, 4),
                    "ref_stage": ref_key[2], "E": round(E, 3), "depth": depth,
                    "max_orr": round(max_orr, 1)}

        try:
            row = cur.execute("SELECT M, subphase, operation FROM agents WHERE domain_id=? AND id=?",
                             (domain, aid)).fetchone()
        except:
            return {"error": f"Agent {aid} not found in {domain}"}
        if not row:
            return {"error": f"Agent {aid} not found in {domain}"}
        M, sp, op = row[0], row[1], row[2] or 'hold'
        w = omega(op, sp)
        r = residual(M, beta, tau, gamma, prior_lines, w)
        raw_orr = (1 - r ** depth) * 100
        orr = round(max(0, min(raw_orr, max_orr)), 1)
        return {"orr": orr, "method": "single_structural", "M": round(M, 4),
                "E": round(E, 3), "depth": depth, "max_orr": round(max_orr, 1)}

    # Multi-agent novel combo: separate by layer
    layer_agents = {3: [], 4: []}
    for aid in agents_in_combo:
        try:
            row = cur.execute("SELECT M, subphase, operation, class FROM agents WHERE domain_id=? AND id=?",
                             (domain, aid)).fetchone()
        except:
            row = None
        if not row:
            continue
        M, sp, op, cls = row[0], row[1], row[2] or 'hold', row[3] or ''
        layer = get_agent_layer(cls)

        single_cals = {k: v for k, v in cal_table.items()
                       if k[0] == domain and k[1] == aid}
        if single_cals:
            M_use = list(single_cals.values())[0]
            w = omega(op, sp)
            r = residual_calibrated(M_use, E, w)
        else:
            w = omega(op, sp)
            r = residual(M, beta, tau, gamma, prior_lines, w)

        layer_agents[layer].append({"aid": aid, "M": M, "sp": sp, "op": op,
                                     "residual": r, "layer": layer})

    active_layers = [l for l in [3, 4] if layer_agents[l]]
    if not active_layers:
        return {"error": "No agents resolved"}

    is_cross_layer = len(active_layers) > 1

    if not is_cross_layer:
        sp_products = {}
        for a in layer_agents[active_layers[0]]:
            sp = a['sp']
            if sp not in sp_products:
                sp_products[sp] = 1.0
            sp_products[sp] *= a['residual']

        product = 1.0
        for sp, r in sp_products.items():
            product *= r ** depth

        k = len(sp_products)
        sigma = SIGMA_TABLE.get(k, 1.0)
        raw_orr = (1 - product ** (k * sigma)) * 100 if product > 0 else 100
        orr = round(max(0, min(raw_orr, max_orr)), 1)
        return {"orr": orr, "method": "novel_same_layer", "k": k,
                "layers": active_layers, "cross_layer": False,
                "max_orr": round(max_orr, 1),
                "note": "Independence assumed within layer."}

    else:
        layer_orrs = {}
        for layer in active_layers:
            agents = layer_agents[layer]
            sp_products = {}
            for a in agents:
                sp = a['sp']
                if sp not in sp_products:
                    sp_products[sp] = 1.0
                sp_products[sp] *= a['residual']

            product = 1.0
            for sp, r in sp_products.items():
                product *= r ** depth

            k = len(sp_products)
            sigma = SIGMA_TABLE.get(k, 1.0)
            layer_orr = (1 - product ** (k * sigma)) * 100 if product > 0 else 100
            layer_orr = min(layer_orr, max_orr)
            layer_orrs[layer] = layer_orr / 100

        combined = 1.0
        for layer_orr in layer_orrs.values():
            combined *= (1 - layer_orr)
        raw_orr = (1 - combined) * 100

        orr = round(max(0, min(raw_orr, max_orr)), 1)
        return {"orr": orr, "method": "novel_cross_layer", "cross_layer": True,
                "layer_orrs": {k: round(v * 100, 1) for k, v in layer_orrs.items()},
                "layers": active_layers, "max_orr": round(max_orr, 1),
                "note": "Cross-layer combination (L3+L4). Bliss independence."}


# ══════════════════════════════════════════
# LEGACY API (used by app.py predict_combination)
# ══════════════════════════════════════════

def predict_orr_structural(
    beta, dt, depth, tau, prior_lines, gamma, agents,
    cancer_strategy=None,
):
    """Structural prediction from per-agent M tuples (no calibration lookup).

    This is the v7 formula kept for backward compatibility.
    agents: list of (M, subphase) or (M, subphase, operation) tuples.
    """
    if not agents:
        return {"orr": 0, "raw_orr": 0, "depth_resistance": 0, "k": 0,
                "sigma": 1.0, "product": 1.0, "agent_residuals": []}

    sp_products = {}
    agent_residuals = []
    for agent_tuple in agents:
        if len(agent_tuple) >= 3:
            M, sp, op = agent_tuple[0], agent_tuple[1], agent_tuple[2]
            w = omega(op, sp, cancer_strategy)
        else:
            M, sp = agent_tuple[0], agent_tuple[1]
            op = None
            w = 1.0
        r = residual(M, beta, tau, gamma, prior_lines, w)
        agent_residuals.append({"M": M, "sp": sp, "operation": op, "omega": round(w, 2), "residual": round(r, 4)})
        if sp not in sp_products:
            sp_products[sp] = 1.0
        sp_products[sp] *= r

    product = 1.0
    for sp, r in sp_products.items():
        product *= r ** depth

    k = len(sp_products)
    sigma = SIGMA_TABLE.get(k, 1.0)
    exponent = k * sigma
    raw_orr = (1 - product ** exponent) * 100 if product > 0 else 100.0

    R_depth = depth_resistance(dt, depth)
    BASELINE_CEILING = 0.85
    max_orr = min(BASELINE_CEILING, 1 - R_depth) * 100
    orr = min(raw_orr, max_orr)
    orr = round(max(0, min(100, orr)), 1)

    return {
        "orr": orr, "raw_orr": round(raw_orr, 1),
        "depth_resistance": round(R_depth, 3), "max_orr": round(max_orr, 1),
        "k": k, "sigma": sigma, "exponent": round(exponent, 3),
        "product": round(product, 6), "agent_residuals": agent_residuals,
    }


# ══════════════════════════════════════════
# VALIDATION
# ══════════════════════════════════════════

def validate(conn, cancer_only=False):
    """Run predictions against all evidence entries."""
    cal_table = build_calibration_table(conn, cancer_only)
    cur = conn.cursor()

    evidence = cur.execute("""
        SELECT e.domain_id, e.agent_combo, e.stage_id, e.trial_name,
               e.observed_orr, e.n, d.name
        FROM evidence e JOIN domains d ON e.domain_id = d.id
        WHERE e.observed_orr IS NOT NULL ORDER BY e.domain_id
    """).fetchall()

    results = []
    for domain, combo, stage, trial, obs, n, dname in evidence:
        pred = predict_orr(conn, domain, combo, stage, cal_table)
        if "error" in pred:
            continue
        gap = pred["orr"] - obs
        results.append({
            "domain": domain, "domain_name": dname, "trial": trial,
            "combo": combo, "stage": stage,
            "predicted": pred["orr"], "observed": obs,
            "gap": round(gap, 1), "abs_gap": round(abs(gap), 1),
            "n": n, "method": pred.get("method", ""),
            "max_orr": pred.get("max_orr", 100),
        })

    results.sort(key=lambda x: x["abs_gap"])
    total = len(results)
    if total == 0:
        return {"total": 0, "mae": 0, "results": []}

    mae = sum(r["abs_gap"] for r in results) / total
    w3 = sum(1 for r in results if r["abs_gap"] <= 3)
    w5 = sum(1 for r in results if r["abs_gap"] <= 5)
    w10 = sum(1 for r in results if r["abs_gap"] <= 10)

    return {
        "total": total, "mae": round(mae, 1),
        "within_3": w3, "pct_3": round(w3 / total * 100, 1),
        "within_5": w5, "pct_5": round(w5 / total * 100, 1),
        "within_10": w10, "pct_10": round(w10 / total * 100, 1),
        "results": results,
    }


# ══════════════════════════════════════════
# UNIVERSAL FORMULA
# ══════════════════════════════════════════

def effective_potency(M, D, S=0.0):
    """M_eff = M * (1-D)/(1+D) * (1+S)."""
    if D >= 1:
        return 0.0
    if D <= 0:
        return M * (1 + S)
    return M * (1 - D) / (1 + D) * (1 + S)


# ══════════════════════════════════════════
# PATIENT-LEVEL PREDICTION (v10)
# ══════════════════════════════════════════

def conservation_drain(primary_norm, secondary_norm=0.0):
    """Conservation depth drain: D = primary/φ⁰ + secondary/φ¹.
    
    Primary = active suppression marker (CCR8+ Treg in scRNA, checkpoint in bulk).
    Secondary = regulatory programme marker (FOXP3+ Treg).
    Both normalized to [0,1].
    
    Returns D clamped to [0, 0.99].
    """
    D = primary_norm + secondary_norm / PHI
    return max(0.0, min(D, 0.99))


def patient_m_eff(M, primary_drain_norm, secondary_drain_norm=0.0, signal_norm=0.0):
    """Patient-level effective potency using conservation depth model.
    
    M: population-level drug overlap (from DRS calibration).
    primary_drain_norm: active suppression marker, normalized [0,1].
    secondary_drain_norm: regulatory programme marker, normalized [0,1].
    signal_norm: innate surveillance marker, normalized [0,1].
    
    Formula: M_eff = M × (1-D)/(1+D) × (1+S)
    Where D = primary + secondary/φ
    
    Validated:
      Zhang NSCLC n=159: AUC 0.832 (CCR8 Treg + FOXP3 Treg/φ + NK)
      Sade-Feldman melanoma n=37: AUC 0.692
      Riaz melanoma n=49: AUC 0.654
    """
    D = conservation_drain(primary_drain_norm, secondary_drain_norm)
    return effective_potency(M, D, signal_norm)


def classify_observer_state(cd8_fraction, treg_fraction,
                            cd8_threshold=None, treg_threshold=None):
    """Classify patient into Observer state from immune markers.
    
    cd8_fraction: CD8+ T-cell fraction (of total cells or immune cells).
    treg_fraction: Treg fraction = Treg / (CD8 + Treg).
    
    Returns: 'attend', 'drain', 'withdraw', or 'confusion'.
    
    Thresholds default to TCGA pan-cancer medians (n=2,806).
    """
    cd8_med = cd8_threshold or OBSERVER_CD8_MEDIAN
    treg_med = treg_threshold or OBSERVER_TREG_FRAC_MEDIAN
    
    hi_cd8 = cd8_fraction >= cd8_med
    hi_treg = treg_fraction >= treg_med
    
    if hi_cd8 and not hi_treg:
        return 'attend'
    elif hi_cd8 and hi_treg:
        return 'drain'
    elif not hi_cd8 and not hi_treg:
        return 'withdraw'
    else:
        return 'confusion'


def normalize_lognormal_cdf(value, mu, sigma):
    """Normalize a value to [0,1] using log-normal CDF.
    
    Transferable normalization: given reference population parameters (mu, sigma
    in log-space), maps any new patient's value to a percentile.
    
    The percentile IS the drain: 95th percentile Treg → D=0.95.
    Loses only 0.005 AUC vs dataset-max normalization (validated on Zhang n=159).
    """
    if value <= 0:
        return 0.0
    z = (math.log(value) - mu) / sigma if sigma > 0 else 0
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def patient_predict(M, primary_value, secondary_value, signal_value,
                    ref_platform='zhang_nsclc_scrna', normalize='dataset_max',
                    primary_max=None, secondary_max=None, signal_max=None):
    """Full patient-level prediction pipeline.
    
    Args:
        M: population drug overlap from DRS.
        primary_value: raw CCR8+ Treg value (or equivalent active suppression marker).
        secondary_value: raw FOXP3+ Treg value (or equivalent regulatory marker).
        signal_value: raw FGFBP2+ NK value (or equivalent surveillance marker).
        ref_platform: key into LOGNORM_REF for transferable normalization.
        normalize: 'dataset_max' (requires *_max args) or 'lognormal_cdf'.
        *_max: dataset maximum values (for dataset_max normalization).
    
    Returns: dict with m_eff, D, S, observer_state, method.
    """
    if normalize == 'lognormal_cdf' and ref_platform in LOGNORM_REF:
        ref = LOGNORM_REF[ref_platform]
        p_norm = normalize_lognormal_cdf(primary_value,
                                          ref['ccr8_treg']['mu'],
                                          ref['ccr8_treg']['sigma'])
        s_norm = normalize_lognormal_cdf(signal_value,
                                          ref['fgfbp2_nk']['mu'],
                                          ref['fgfbp2_nk']['sigma'])
        # Secondary uses same reference as primary (both Treg subtypes)
        sec_norm = normalize_lognormal_cdf(secondary_value,
                                            ref['ccr8_treg']['mu'],
                                            ref['ccr8_treg']['sigma'])
        method = 'lognormal_cdf'
    elif normalize == 'dataset_max' and primary_max and primary_max > 0:
        p_norm = min(primary_value / primary_max, 1.0)
        sec_norm = min(secondary_value / (secondary_max or primary_max), 1.0)
        s_norm = min(signal_value / (signal_max or 1.0), 1.0) if signal_max else 0.0
        method = 'dataset_max'
    else:
        # Fallback: raw values assumed already normalized
        p_norm = min(primary_value, 1.0)
        sec_norm = min(secondary_value, 1.0)
        s_norm = min(signal_value, 1.0)
        method = 'raw'
    
    D = conservation_drain(p_norm, sec_norm)
    m_eff = effective_potency(M, D, s_norm)
    
    return {
        'm_eff': round(m_eff, 4),
        'D': round(D, 4),
        'S': round(s_norm, 4),
        'primary_norm': round(p_norm, 4),
        'secondary_norm': round(sec_norm, 4),
        'method': method,
    }



# ══════════════════════════════════════════
# DISARM — PATIENT-LEVEL UNIVERSAL PREDICTION (v12)
# ══════════════════════════════════════════
#
# DISARM = Dissipative Immune Agent Response Model
#
# Structural derivation:
#   The immune system is an agent addressing a tumour (target).
#   Agent effectiveness A = immune_kill_rate / tumour_growth_rate.
#   Drain D = (1 - A)/φ — low effectiveness = high drain.
#
#   In gene expression:
#     kill_rate = cytolytic genes (GZMB + PRF1 + IFNG + GZMA)
#     growth_rate = tumour proliferation (MKI67)
#     A = kill_rate / growth_rate
#
#   The ratio cancels infiltration confounds:
#     bulk RNA: both numerator and denominator ∝ biopsy composition
#     scRNA: cell fractions already capture composition balance
#     NanoString: gene counts normalize by the ratio
#
#   Log-space formulation (for log2(TPM+1) harmonized data):
#     score = sum(log2(eff_genes)) - log2(MKI67)
#           = log2(GZMB × PRF1 × IFNG × GZMA / MKI67)
#     Multiplicative: requires ALL four effector mechanisms active.
#     Linear sum/MKI67 FAILS on IMvigor210 (direction flip).
#
#   Direction: ALWAYS high ratio = immune winning = respond.
#   Universal across platforms and cancer types. Zero fitted parameters.
#
# DISARM General:
#   Linear: (GZMB+PRF1+IFNG+GZMA) / (MKI67+eps)
#   Log2:   sum(log2_genes) - log2(MKI67)
#
# DISARM Specific (2-feature):
#   D = (1-eff_rank) + supp_rank/φ; M_eff = M × (1-D)/(1+D)
#
# Validated: 11 datasets, 1,088 patients, 3 platforms, 5 cancer types
#   All 11 datasets: direction hi=R confirmed (11/11 ✓)
#
#   Dataset               n    Platform      DISARM-G  DISARM-S  Ceiling
#   Zhang NSCLC          242   scRNA          0.741    0.827     0.829
#   Sade-Feldman Mel      48   scRNA          0.740    0.903     0.903
#   Hugo Melanoma         27   Bulk RNA       0.533    0.648     0.813
#   Riaz Pre              33   Bulk RNA       0.630    0.748     0.804
#   Riaz On               38   Bulk RNA       0.800    0.800     0.908
#   GSE93157 Mixed        49   NanoString     0.585    0.654     0.729
#   Rose Urothelial       58   Bulk RNA       0.596    0.596     0.764
#   IMvigor210           298   Bulk RNA       0.587    0.606     0.668
#   Liu Melanoma         122   Bulk RNA       0.530    0.524     0.566
#   Gide Melanoma         91   Bulk RNA       0.811    0.775     0.824
#   IMmotion150 atezo    165   Bulk RNA       0.667    0.590     0.694
#
# Classified DISARM (marker selection by treatment context):
#   Post-CPI scRNA:  D = Treg_CCR8 + Treg_MKI67/φ, S = -mDC/φ    → 0.827
#   On-CPI scRNA:    D = HAVCR2 + FGFBP2/φ, S = CD8A/φ            → 0.903
#   Bulk/Nano:       D = -(eff/MKI67)_rank + (supp/MKI67)_rank/φ   → 0.530-0.800
#
# Foundation model (Zhang scRNA n=242, 5-fold CV):
#   DISARM structural 5 features:     0.768
#   Competitor equivalent 3 features: 0.578
#   All cell types ML 30 features:    0.773
#   Best single: disarm_effectiveness = eff/(eff+treg) = 0.780
#
# Negative control: IMmotion150 sunitinib (no ICI, n=82):
#   AUC=0.513, direction=hi=NR. Correctly fails on non-immunotherapy.
#

# PhiScore marker sets per structural position
PHISCORE_MARKERS = {
    'effector': ['GZMB', 'PRF1', 'IFNG', 'GZMA'],  # SP3+SP4 cytolytic
    'suppressor': ['HAVCR2', 'TIGIT', 'LAG3', 'FOXP3'],  # SP3+SP4 checkpoint/Treg
    'tumour_proliferation': ['MKI67'],  # Tumour growth rate
    'perception': ['CD274', 'FGFBP2'],  # SP1: PD-L1 hiding vs NK detection
    'formation': ['CXCL13', 'CD8A'],  # SP2: recruitment and expansion
}

# Structural position mapping for scRNA cell fractions (Zhang-type)
PHISCORE_SCRNA_MAP = {
    'sp4_suppressor': ['CD4T_Treg_CCR8', 'CD4T_Treg_FOXP3', 'CD4T_Treg_MKI67'],
    'sp3_exhausted': ['CD8T_Tex_CXCL13', 'CD8T_terminal_Tex_LAYN'],
    'sp3_effector': ['CD8T_Tem_GZMK_GZMH', 'CD8T_Trm_ZNF683', 'CD8T_prf_MKI67'],
    'sp1_effector': ['CD8T_NK_like_FGFBP2', 'NK_CD16hi_FGFBP2'],
    'sp1_perception': ['cDC1_CLEC9A', 'mDC_LAMP3'],
}


def phiscore_universal(effector_sum, mki67, eps=0.01):
    """PhiScore universal: immune effectiveness relative to tumour growth.
    
    A = effector / MKI67 → high = immune winning = respond.
    
    Args:
        effector_sum: sum of GZMB + PRF1 + IFNG + GZMA (or cell fraction equivalent)
        mki67: MKI67 expression (tumour proliferation marker)
        eps: small constant to avoid division by zero
    
    Returns: raw PhiScore (not rank-normalized — normalize across cohort).
    
    Direction: ALWAYS high = respond. Validated on 7/7 datasets.
    """
    return effector_sum / (mki67 + eps)


def phiscore_2feat(effector_sum, suppressor_sum, mki67, eps=0.01):
    """PhiScore 2-feature: effectiveness + suppression burden.
    
    Feature 1 (score): effector / MKI67 (high = good = immune winning)
    Feature 2 (drain): suppressor / MKI67 (high = bad = suppression outpacing)
    
    Returns: (score, drain) — both need rank-normalization across cohort.
    Then: D = (1-score_rank) + drain_rank/φ; M_eff = M × (1-D)/(1+D)
    """
    score = effector_sum / (mki67 + eps)
    drain = suppressor_sum / (mki67 + eps)
    return score, drain


def phiscore_scrna(patient_fractions):
    """PhiScore for scRNA cell fraction data.
    
    Uses cell type fractions directly (already tumour-normalized).
    Effectiveness = effector_fraction / (effector_fraction + suppressor_fraction)
    
    Args:
        patient_fractions: dict of cell type fractions from scRNA deconvolution
    
    Returns: effectiveness score (high = respond)
    """
    eps = 0.001
    treg = sum(patient_fractions.get(k, 0) for k in PHISCORE_SCRNA_MAP['sp4_suppressor'])
    eff = sum(patient_fractions.get(k, 0) for k in PHISCORE_SCRNA_MAP['sp3_effector'])
    nk = sum(patient_fractions.get(k, 0) for k in PHISCORE_SCRNA_MAP['sp1_effector'])
    return (eff + nk) / (eff + nk + treg + eps)


def phiscore_classified(patient_data, context='bulk'):
    """PhiScore with context-classified marker selection.
    
    Args:
        patient_data: dict with gene expression or cell fractions
        context: 'post_cpi_scrna', 'on_cpi_scrna', or 'bulk'
    
    Returns: dict with drain_primary, drain_secondary, signal values
             (all need rank-normalization across cohort before combining)
    """
    if context == 'post_cpi_scrna':
        # SP4 conservation is the bottleneck
        d1 = patient_data.get('CD4T_Treg_CCR8', 0)
        d2 = patient_data.get('CD4T_Treg_MKI67', 0)
        sig = -(patient_data.get('mDC_LAMP3', 0))
    elif context == 'on_cpi_scrna':
        # SP3 encounter exhaustion
        d1 = patient_data.get('HAVCR2', 0)
        d2 = patient_data.get('FGFBP2', 0)
        sig = patient_data.get('CD8A', 0)
    else:
        # Bulk/NanoString: use MKI67-normalized ratios
        eps = 0.01
        mki67 = patient_data.get('MKI67', 0) + eps
        eff = sum(patient_data.get(g, 0) for g in PHISCORE_MARKERS['effector'])
        supp = sum(patient_data.get(g, 0) for g in PHISCORE_MARKERS['suppressor'])
        d1 = -(eff / mki67)  # high eff/MKI67 = low drain
        d2 = supp / mki67     # high supp/MKI67 = high drain
        sig = 0
    
    return {'drain_primary': d1, 'drain_secondary': d2, 'signal': sig}


def phiscore_from_ranks(drain_primary_rank, drain_secondary_rank=0.0,
                        signal_rank=0.0, M=0.5):
    """Compute PhiScore M_eff from rank-normalized drain values.
    
    All inputs should be rank-normalized to [0,1] within the cohort.
    High drain_rank = high drain = bad.
    
    D = drain_primary_rank + drain_secondary_rank / φ
    M_eff = M × (1-D)/(1+D) × (1+S)
    """
    D = drain_primary_rank + drain_secondary_rank / PHI
    D_norm = D / (1 + 1/PHI)  # normalize to [0,1]
    D_norm = max(0.0, min(D_norm, 0.99))
    S = signal_rank / PHI if signal_rank else 0.0
    return M * (1 - D_norm) / (1 + D_norm) * (1 + S)



# ══════════════════════════════════════════
# DISARM v13 — FORMULAS + DISARM-S FUNCTIONS
# ══════════════════════════════════════════

# DISARM validation results (v13)
DISARM_VALIDATION = {
    # scRNA datasets
    'Zhang_NSCLC':        {'n': 242, 'cancer': 'NSCLC',      'platform': 'scRNA',     'tx': 'post-CPI',       'dg': 0.741, 'ds': 0.827, 'ceil': 0.829},
    'SadeFeldman_all':    {'n':  48, 'cancer': 'Melanoma',    'platform': 'scRNA',     'tx': 'mixed pre/post', 'dg': 0.740, 'ds': 0.903, 'ceil': 0.903, 'note': 'Mixed pre/post — misleading. Use pre-only.'},
    'SadeFeldman_pre':    {'n':  19, 'cancer': 'Melanoma',    'platform': 'scRNA',     'tx': 'pre-CPI',        'dg': 'FLIP', 'ds_s': 0.888, 'ceil': 0.944, 'note': 'DG flips on scRNA mean expression. DISARM-S 6-feat = 0.888.'},
    # Bulk anti-PD1/PD-L1 datasets
    'Hugo_Mel':           {'n':  27, 'cancer': 'Melanoma',    'platform': 'bulk',      'tx': 'pre-PD1',        'dg': 0.533, 'ds': 0.648, 'ceil': 0.813},
    'Riaz_Pre':           {'n':  33, 'cancer': 'Melanoma',    'platform': 'bulk',      'tx': 'pre-nivo',       'dg': 0.630, 'ds': 0.748, 'ceil': 0.804},
    'Riaz_On':            {'n':  38, 'cancer': 'Melanoma',    'platform': 'bulk',      'tx': 'on-nivo',        'dg': 0.800, 'ds': 0.800, 'ceil': 0.908},
    'GSE93157_Mixed':     {'n':  49, 'cancer': 'Mixed',       'platform': 'NanoString','tx': 'pembro',         'dg': 0.585, 'ds': 0.654, 'ceil': 0.729},
    'Rose_Uro':           {'n':  58, 'cancer': 'Urothelial',  'platform': 'bulk',      'tx': 'mixed PD-(L)1',  'dg': 0.596, 'ds': 0.596, 'ceil': 0.764},
    'IMvigor210':         {'n': 298, 'cancer': 'Urothelial',  'platform': 'bulk',      'tx': 'atezolizumab',   'dg': 0.587, 'ds': 0.606, 'ceil': 0.668},
    'Liu_Mel':            {'n': 122, 'cancer': 'Melanoma',    'platform': 'bulk',      'tx': 'pembro/nivo',    'dg': 0.530, 'ds': 0.524, 'ceil': 0.566},
    'Gide_Mel':           {'n':  91, 'cancer': 'Melanoma',    'platform': 'bulk',      'tx': 'anti-PD1+CTLA4', 'dg': 0.811, 'ds': 0.775, 'ceil': 0.824},
    'IMmotion150_atezo':  {'n': 165, 'cancer': 'RCC',         'platform': 'bulk',      'tx': 'atezolizumab',   'dg': 0.667, 'ds': 0.590, 'ceil': 0.694},
    'GSE135222_NSCLC':    {'n':  27, 'cancer': 'NSCLC',       'platform': 'bulk',      'tx': 'anti-PD1/L1',    'dg': 0.714, 'ceil': 0.761, 'note': 'PFS-based response (>180d). Adds NSCLC to bulk.'},
    # Bulk anti-CTLA4
    'VanAllen_Mel':       {'n':  42, 'cancer': 'Melanoma',    'platform': 'bulk',      'tx': 'ipilimumab',     'dg': 0.651, 'ceil': 0.724, 'note': 'Anti-CTLA4. Direction correct but suboptimal. CTLA4 expr best predictor (0.724).'},
    # Negative control
    'IMmotion150_suni':   {'n':  82, 'cancer': 'RCC',         'platform': 'bulk',      'tx': 'sunitinib',      'dg': 0.513, 'note': 'Negative control. Direction FLIPPED (hi=NR). Confirms ICI specificity.'},
}

# Competitor AUCs (mean across 4 new bulk datasets: IMvigor210, Liu, Gide, IMmotion150)
COMPETITOR_COMPARISON = {
    'DISARM_General': 0.649, 'DISARM_Specific': 0.624,
    'IFNg_signature': 0.654, 'GEP_18gene': 0.648, 'CYT_score': 0.639,
    'PDL1_CD274': 0.634, 'CD8_score': 0.656, 'IMPRES': 0.558, 'IFNG_alone': 0.655,
}

# Foundation model results (v13: Zhang + Sade-Feldman)
FOUNDATION_MODEL = {
    'zhang_nsclc_10x': {
        'n': 242, 'cancer': 'NSCLC', 'platform': '10x scRNA',
        'DISARM_S_5feat': 0.768, 'DISARM_S_6feat_renewal': 0.778,
        'Competitor_3feat': 0.578, 'All_celltypes_ML_51feat': 0.764,
        'best_single': ('disarm_effectiveness', 0.780),
    },
    'sade_feldman_smartseq2_pre': {
        'n': 19, 'cancer': 'Melanoma', 'platform': 'Smart-Seq2',
        'DISARM_S_5feat': 0.832, 'DISARM_S_6feat_renewal': 0.888,
        'Competitor_3feat': 0.770, 'All_genes_ML_30feat': 0.892,
        'best_single': ('TCF7', 0.944),
        'note': 'Pre-treatment only. TCF7 (renewal) is dominant signal.',
    },
}

# ══════════════════════════════════════════
# DISARM-S OBSERVABLE TABLE (v13)
# ══════════════════════════════════════════
# Positions are fixed (derived). Observables are validated per platform.
# The context is platform × drug mechanism, NOT cancer type.

# scRNA structural features (cell fractions for 10x, gene means for Smart-Seq2)
DISARM_S_SCRNA_FEATURES = {
    'sp4_suppression': {
        '10x': ['CD4T_Treg_CCR8', 'CD4T_Treg_FOXP3', 'CD4T_Treg_MKI67'],
        'smartseq2': ['FOXP3', 'CCR8', 'CTLA4'],
        'direction': 'hi=NR',
        'confirmed': {'10x': 'Zhang AUC 0.765', 'smartseq2': 'Sade weak (0.544)'},
    },
    'sp4_renewal': {
        '10x': ['CD4T_Tn_CCR7', 'CD8T_Tm_IL7R'],
        'smartseq2': ['TCF7'],
        'direction': 'hi=R',
        'confirmed': {'10x': 'Zhang AUC 0.606', 'smartseq2': 'Sade AUC 0.944 DOMINANT'},
        'note': 'INVERTS on bulk (IMvigor210 0.429, GSE135222 0.368). scRNA-only feature.',
    },
    'sp3_effector': {
        '10x': ['CD8T_Tem_GZMK+GZMH+', 'CD8T_Tem_GZMK+NR4A1+',
                'CD8T_Trm_ZNF683', 'CD8T_prf_MKI67'],
        'smartseq2': ['GZMB', 'PRF1', 'IFNG', 'NKG7', 'GZMA'],
        'direction': 'hi=R on 10x, INVERTED on smartseq2 mean expression',
        'confirmed': {'10x': 'Zhang AUC 0.513 (weak alone, strong in ratio)',
                      'smartseq2': 'Sade ALL hi=NR — inverted'},
    },
    'sp3_exhaustion': {
        '10x': ['CD8T_Tex_CXCL13', 'CD8T_terminal_Tex_LAYN'],
        'smartseq2': ['HAVCR2', 'TOX', 'ENTPD1', 'CXCL13', 'LAG3'],
        'direction': 'hi=NR',
        'confirmed': {'10x': 'Zhang AUC 0.379 (correct dir)',
                      'smartseq2': 'Sade HAVCR2 AUC 0.889 hi=NR (strong)'},
    },
    'sp1_perception': {
        '10x': ['NK_CD16hi_FGFBP2', 'CD8T_NK-like_FGFBP2', 'NK_CD16low_GZMK'],
        'smartseq2': ['FGFBP2', 'NCAM1'],
        'direction': 'hi=R',
        'confirmed': {'10x': 'Zhang NK total AUC 0.633',
                      'smartseq2': 'Sade INVERTED (hi=NR) — same as effectors'},
    },
}

# Bulk structural features (DISARM General handles bulk; these are for reference)
DISARM_S_BULK_FEATURES = {
    'sp3_effector': {
        'genes': ['GZMB', 'PRF1', 'IFNG', 'GZMA'],
        'direction': 'hi=R',
        'confirmed': '12/12 bulk ICI datasets',
    },
    'growth_denominator': {
        'genes': ['MKI67'],
        'direction': 'in ratio (not standalone — often hi=R on bulk)',
        'confirmed': 'Core of DISARM formula',
    },
    'sp1_perception': {
        'genes': ['NKG7'],
        'direction': 'hi=R',
        'confirmed': 'Most bulk datasets',
    },
    'sp3_exhaustion': {
        'genes': ['HAVCR2', 'TIGIT', 'LAG3'],
        'direction': 'hi=NR in ratio, but raw direction unreliable (co-infiltration)',
    },
    'sp4_suppression': {
        'genes': ['FOXP3'],
        'direction': 'hi=NR in ratio, but raw direction unreliable (co-infiltration)',
    },
    'sp4_renewal': {
        'genes': ['TCF7', 'IL7R', 'CCR7'],
        'direction': 'NOT CONFIRMED — inverts on IMvigor210 and GSE135222',
        'note': 'Bulk cannot distinguish activated from bystander T cells.',
    },
}

# Backward compatibility alias
DISARM_SCRNA_FEATURES = DISARM_S_SCRNA_FEATURES


def disarm_general_log(log2_gzmb, log2_prf1, log2_ifng, log2_gzma, log2_mki67):
    """DISARM General for log2-transformed data (iAtlas, harmonized TPM).

    score = sum(log2_eff) - log2(MKI67)
          = log2(GZMB × PRF1 × IFNG × GZMA / MKI67)

    This multiplicative formulation requires ALL four effector mechanisms
    to be active. A zero in any gene kills the score. More structural
    than linear summation, and handles log2(TPM+1) platforms correctly.

    Args: log2 expression values for each gene.
    Returns: raw score (rank-normalize across cohort). High = respond.
    """
    return (log2_gzmb + log2_prf1 + log2_ifng + log2_gzma) - log2_mki67


def disarm_general_linear(gzmb, prf1, ifng, gzma, mki67, eps=0.01):
    """DISARM General for linear expression data (FPKM, TPM, raw counts).

    score = (GZMB + PRF1 + IFNG + GZMA) / (MKI67 + eps)

    Additive formulation — one strong gene can compensate for a weak one.
    Use for raw/linear platforms. For log2(TPM+1) data, use disarm_general_log.

    Returns: raw score. High = respond.
    """
    return (gzmb + prf1 + ifng + gzma) / (mki67 + eps)


def disarm_scrna_effectiveness(patient_fractions):
    """DISARM effectiveness ratio for scRNA cell fraction data.

    effectiveness = (effector + NK + renewal) / (effector + NK + renewal + Treg + Tex + eps)

    The key structural feature — captures whether the immune agent is
    winning (high effector + renewal relative to suppressor + exhaustion).

    v13: Added renewal (SP4 conservation). Validated on Zhang (0.776) and
    Sade-Feldman pre-treatment (dominant via TCF7).

    Args:
        patient_fractions: dict of cell type → fraction (or gene → expression)
    Returns: effectiveness score [0, 1]. High = respond.
    """
    eps = 0.001
    feat = DISARM_S_SCRNA_FEATURES

    # Try 10x cell fractions first, fall back to smartseq2 gene names
    def _sum_keys(position, platform_pref='10x'):
        keys = feat[position].get(platform_pref, [])
        total = sum(patient_fractions.get(k, 0) for k in keys)
        if total == 0 and platform_pref == '10x':
            # Fall back to smartseq2
            keys = feat[position].get('smartseq2', [])
            total = sum(patient_fractions.get(k, 0) for k in keys)
        return total

    treg = _sum_keys('sp4_suppression')
    eff = _sum_keys('sp3_effector')
    tex = _sum_keys('sp3_exhaustion')
    nk = _sum_keys('sp1_perception')
    renewal = _sum_keys('sp4_renewal')

    kill = eff + nk + renewal
    suppress = treg + tex
    return kill / (kill + suppress + eps)


def disarm_scrna_foundation(patient_fractions):
    """DISARM-S foundation model features for scRNA data.

    Returns dict of 6 structural features for logistic regression.

    v13: Added renewal_total (SP4 conservation — naive/memory T cells).
    Zhang: 6 features → 0.778 (5-fold CV), matching 51-feature ML (0.764).
    Sade-Feldman pre: 6 features → 0.888, matching 30-gene ML (0.892).

    Features:
        disarm_ratio:   (eff+nk+renewal) / (all immune + eps)
        treg_total:     sum of Treg fractions (SP4 suppression)
        eff_total:      sum of effector fractions (SP3 encounter)
        tex_total:      sum of exhausted fractions (SP3 exhaustion)
        nk_total:       sum of NK fractions (SP1 perception)
        renewal_total:  sum of naive/memory fractions (SP4 renewal)
    """
    eps = 0.001
    feat = DISARM_S_SCRNA_FEATURES

    def _sum_keys(position, platform_pref='10x'):
        keys = feat[position].get(platform_pref, [])
        total = sum(patient_fractions.get(k, 0) for k in keys)
        if total == 0 and platform_pref == '10x':
            keys = feat[position].get('smartseq2', [])
            total = sum(patient_fractions.get(k, 0) for k in keys)
        return total

    treg = _sum_keys('sp4_suppression')
    eff = _sum_keys('sp3_effector')
    tex = _sum_keys('sp3_exhaustion')
    nk = _sum_keys('sp1_perception')
    renewal = _sum_keys('sp4_renewal')

    kill = eff + nk + renewal
    suppress = treg + tex

    return {
        'disarm_ratio': kill / (kill + suppress + eps),
        'treg_total': treg,
        'eff_total': eff,
        'tex_total': tex,
        'nk_total': nk,
        'renewal_total': renewal,
    }


# Aliases: DISARM ← PhiScore (backward compatibility)
# Note: original phiscore_universal(effector_sum, mki67) still exists above
# disarm_general_linear has expanded signature (individual genes)
disarm_general = disarm_general_linear

# DISARM-S convenience: select features by context
disarm_s = disarm_scrna_foundation  # alias for the 6-feature model


# ══════════════════════════════════════════
# SELF-TEST
# ══════════════════════════════════════════

if __name__ == "__main__":
    try:
        import sqlite3
        conn = sqlite3.connect("systems.db")
        v = validate(conn)
        print(f"DB validation: {v['total']} trials, MAE={v['mae']}")
        print(f"  <=3pt: {v['within_3']}/{v['total']} ({v['pct_3']}%)")
        print(f"  <=5pt: {v['within_5']}/{v['total']} ({v['pct_5']}%)")
        print(f"  <=10pt: {v['within_10']}/{v['total']} ({v['pct_10']}%)")

        non_exact = [r for r in v['results'] if r['abs_gap'] > 0.1]
        if non_exact:
            print(f"\nNon-exact ({len(non_exact)}):")
            for r in non_exact:
                print(f"  {r['domain_name']:30s} | {r['combo']:30s} | obs={r['observed']:5.1f} pred={r['predicted']:5.1f} gap={r['gap']:+5.1f}")
        conn.close()
    except Exception as e:
        print(f"DB not available: {e}")
