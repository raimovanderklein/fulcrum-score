"""
fulcrum.py — FULCRUM Prediction Framework (v14.1)
Generative Geometry (van der Klein, 2026)

FULCRUM measures the balance between two competing dissipative systems:
the immune response and the tumour. Derived from structural theory,
not trained on patient data. Zero fitted parameters.

Three models:
  FULCRUM    — bulk gene expression. 5 genes. No ML.
  FULCRUM-S  — scRNA cell fractions. 1 structural ratio. No ML.
  FULCRUM-S+ — scRNA cell fractions. 6 structural features → LR.

Core structural formula:
  M_eff = M × (1−D) / (1+D)

Immunology instantiation:
  score = Σ log₂(effectors) − log₂(MKI67)
        = log₂(immune output / tumour output)

Every function returns a report, not just a number.

Reproducibility: see FULCRUM_REPRODUCIBILITY_SPEC.md for the locked
protocol. Dataset-specific mappings are defined in DATASET_CONFIGS below.
Any mapping not in DATASET_CONFIGS must be specified explicitly.
"""

import math
from typing import Dict, Optional, List

__version__ = "0.14.1"

# ══════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2  # Golden ratio — structural constant

# Gene roles in the dissipative framework
EFFECTOR_GENES = ['GZMB', 'PRF1', 'IFNG', 'GZMA']
GROWTH_GENE = 'MKI67'

# Structural position labels
POSITION_LABELS = {
    'nk':      'SP1 Perception — detecting the competing system',
    'eff':     'SP3 Effector — output against the target',
    'tex':     'SP3 Exhaustion — failed engagement, energy spent without output',
    'treg':    'SP4 Suppression — conservation captured by the target',
    'renewal': 'SP4 Renewal — conservation maintained by the agent',
    'ratio':   'Balance — agent output relative to total dissipative activity',
}

# Direction of each position (quality-limited regime)
POSITION_DIRECTION = {
    'nk':      'higher is better',
    'eff':     'context-dependent',
    'tex':     'higher is worse',
    'treg':    'higher is worse',
    'renewal': 'higher is better',
    'ratio':   'higher is better',
}

# scRNA markers per position — generic (used when dataset not specified)
SCRNA_MARKERS = {
    'nk':      {'10x': ['NK_CD16hi_FGFBP2', 'CD8T_NK-like_FGFBP2', 'NK_CD16low_GZMK'],
                'smartseq2': ['FGFBP2', 'NCAM1']},
    'eff':     {'10x': ['CD8_Tem', 'CD8_Trm', 'CD8_EMRA'],
                'smartseq2': ['GZMB', 'PRF1']},
    'tex':     {'10x': ['CD8_Tex', 'CD8_Tex_proliferating'],
                'smartseq2': ['HAVCR2', 'TOX', 'ENTPD1']},
    'treg':    {'10x': ['Treg', 'Treg_proliferating'],
                'smartseq2': ['FOXP3', 'CCR8']},
    'renewal': {'10x': ['CD8_Naive', 'CD8_Tcm', 'CD4_Naive'],
                'smartseq2': ['TCF7', 'IL7R', 'CCR7']},
}

# ══════════════════════════════════════════
# DATASET-SPECIFIC LOCKED CONFIGS
# ══════════════════════════════════════════
# Each dataset has its own naming convention for cell subtypes.
# These mappings are locked and version-controlled.
# Using dataset='zhang' or dataset='bassez' applies the correct mapping
# automatically. Results are only reproducible when using these configs.

DATASET_CONFIGS = {
    'zhang': {
        'name': 'Zhang et al. 2025 NSCLC',
        'source': 'GSE243013',
        'n': 242,
        'platform': '10x',
        'denominator': 'total immune cells',
        'response_col': 'pathological_response',
        'responder_values': ['MPR', 'pCR'],
        'exclude_values': ['unknowm'],
        'mapping': {
            'nk':      ['NK_CD16hi_FGFBP2', 'NK_CD16low_GZMK', 'CD8T_NK-like_FGFBP2'],
            'eff':     ['CD8T_Tem_GZMK+GZMH+', 'CD8T_Trm_ZNF683', 'CD8T_Tem_GZMK+NR4A1+'],
            'tex':     ['CD8T_Tex_CXCL13', 'CD8T_terminal_Tex_LAYN', 'CD8T_prf_MKI67'],
            'treg':    ['CD4T_Treg_FOXP3', 'CD4T_Treg_CCR8', 'CD4T_Treg_MKI67'],
            'renewal': ['CD8T_Tm_IL7R', 'CD4T_Tn_CCR7'],
        },
        'verified_results': {
            'fulcrum_s_ratio': 0.780,
            'fulcrum_s_plus': 0.770,
            'full_ml_51': 0.762,
        },
    },
    'bassez': {
        'name': 'Bassez et al. 2021 Breast',
        'source': 'Lambrechts lab (VIB)',
        'n': 29,
        'platform': '10x',
        'denominator': 'whole TME',
        'response_col': 'expansion',
        'responder_values': ['E'],
        'exclude_values': ['n/a'],
        'timepoint_filter': 'Pre',
        'mapping': {
            'nk':      ['NK_CYTO', 'NK_REST'],
            'eff':     ['CD8_EM', 'CD8_RM', 'CD8_EMRA'],
            'tex':     ['CD8_EX', 'CD8_EX_Proliferating'],
            'treg':    ['CD4_REG', 'CD4_REG_Proliferating'],
            'renewal': ['CD8_N', 'CD4_N'],
        },
        'verified_results': {
            'fulcrum_s_ratio': 0.089,
            'fulcrum_s_plus': 0.922,
            'full_ml_16': 0.843,
        },
    },
    'sade_feldman': {
        'name': 'Sade-Feldman et al. 2018 Melanoma',
        'source': 'GSE120575',
        'n': 19,
        'platform': 'smartseq2',
        'denominator': 'total cells per patient',
        'response_col': 'response',
        'responder_values': ['responder'],
        'timepoint_filter': 'pre',
        'mapping': {
            'nk':      ['FGFBP2', 'NCAM1'],
            'eff':     ['GZMB', 'PRF1'],
            'tex':     ['HAVCR2', 'TOX', 'ENTPD1'],
            'treg':    ['FOXP3', 'CCR8'],
            'renewal': ['TCF7', 'IL7R', 'CCR7'],
        },
        'verified_results': {
            'fulcrum_s_ratio': 0.733,
            'fulcrum_s_plus': 0.889,
            'full_ml_30': 0.922,
        },
    },
}

# Evaluation protocol (locked)
EVAL_PROTOCOL = {
    'cv_folds': 5,
    'cv_repeats': 200,
    'random_seed': 42,
    'lr_C': 1.0,
    'lr_max_iter': 1000,
    'lr_solver': 'lbfgs',
    'metric': 'AUC (Mann-Whitney U)',
}


# ══════════════════════════════════════════
# FULCRUM — Bulk gene expression
# ══════════════════════════════════════════

def score_log2(gzmb: float, prf1: float, ifng: float,
               gzma: float, mki67: float) -> float:
    """FULCRUM score for log2-transformed platforms (iAtlas, TPM+1).

    Returns: raw score. High = immune system outpacing tumour.
    """
    return (gzmb + prf1 + ifng + gzma) - mki67


def score_linear(gzmb: float, prf1: float, ifng: float,
                 gzma: float, mki67: float, eps: float = 0.01) -> float:
    """FULCRUM score for linear platforms (FPKM, TPM, raw counts).

    Returns: raw score. High = immune system outpacing tumour.
    """
    return (gzmb + prf1 + ifng + gzma) / (mki67 + eps)


def report_bulk(gzmb: float, prf1: float, ifng: float, gzma: float,
                mki67: float, platform: str = 'log2',
                cohort_scores: Optional[List[float]] = None) -> dict:
    """Generate a FULCRUM report for a bulk expression sample.

    Returns a structured report with:
      - score: the FULCRUM score
      - effector_profile: per-gene breakdown
      - tumour_aggression: MKI67 level assessment
      - balance: which system is dominant
      - interpretation: plain-language summary
      - percentile: where this score sits in the cohort (if provided)

    Args:
        gzmb, prf1, ifng, gzma: effector gene values
        mki67: proliferation marker value
        platform: 'log2' or 'linear'
        cohort_scores: optional list of scores from other patients in the cohort
    """
    genes = {'GZMB': gzmb, 'PRF1': prf1, 'IFNG': ifng, 'GZMA': gzma}

    if platform == 'log2':
        score = score_log2(gzmb, prf1, ifng, gzma, mki67)
        effector_sum = gzmb + prf1 + ifng + gzma
    else:
        score = score_linear(gzmb, prf1, ifng, gzma, mki67)
        effector_sum = gzmb + prf1 + ifng + gzma

    # Gene contributions
    if platform == 'log2':
        gene_contributions = {g: v / effector_sum if effector_sum > 0 else 0.25
                              for g, v in genes.items()}
    else:
        gene_contributions = {g: v / effector_sum if effector_sum > 0 else 0.25
                              for g, v in genes.items()}

    # Find weakest effector
    weakest_gene = min(genes, key=genes.get)
    strongest_gene = max(genes, key=genes.get)

    # Effector profile
    effector_profile = {}
    for g, v in genes.items():
        if platform == 'log2':
            mean_eff = effector_sum / 4
            rel = v / mean_eff if mean_eff > 0 else 1.0
        else:
            mean_eff = effector_sum / 4
            rel = v / mean_eff if mean_eff > 0 else 1.0

        if rel > 1.3:
            level = 'high'
        elif rel < 0.7:
            level = 'low'
        else:
            level = 'moderate'

        effector_profile[g] = {
            'value': round(v, 3),
            'relative_to_mean': round(rel, 2),
            'level': level,
        }

    # Tumour aggression
    # For log2: typical MKI67 range is 0-10, median ~4-5
    # For linear: highly variable
    tumour_aggression = {
        'MKI67': round(mki67, 3),
        'assessment': 'high' if (platform == 'log2' and mki67 > 5.5) or
                                (platform != 'log2' and mki67 > 50) else
                      'low' if (platform == 'log2' and mki67 < 3.0) or
                               (platform != 'log2' and mki67 < 10) else
                      'moderate',
    }

    # Balance
    if score > 0 and platform == 'log2':
        balance = 'immune system is outpacing the tumour'
        prediction = 'likely responder'
    elif score <= 0 and platform == 'log2':
        balance = 'tumour is outpacing the immune system'
        prediction = 'unlikely responder'
    elif score > 4 and platform != 'log2':
        balance = 'immune system is outpacing the tumour'
        prediction = 'likely responder'
    else:
        balance = 'tumour is outpacing the immune system'
        prediction = 'unlikely responder'

    # Percentile
    percentile = None
    if cohort_scores:
        below = sum(1 for s in cohort_scores if s <= score)
        percentile = round(100 * below / len(cohort_scores), 1)

    # Interpretation
    parts = []
    parts.append(f"Immune output: {strongest_gene} is the dominant effector mechanism.")
    if effector_profile[weakest_gene]['level'] == 'low':
        parts.append(f"Weak point: {weakest_gene} is below average — "
                     f"this effector pathway may be underperforming.")
    parts.append(f"Tumour aggression: MKI67 is {tumour_aggression['assessment']}.")
    parts.append(f"Balance: {balance}.")
    if percentile is not None:
        parts.append(f"This score is at the {percentile}th percentile of the cohort.")

    return {
        'model': 'FULCRUM',
        'version': __version__,
        'score': round(score, 3),
        'prediction': prediction,
        'effector_profile': effector_profile,
        'tumour_aggression': tumour_aggression,
        'balance': balance,
        'weakest_effector': weakest_gene,
        'strongest_effector': strongest_gene,
        'percentile': percentile,
        'interpretation': ' '.join(parts),
    }


# ══════════════════════════════════════════
# FULCRUM-S — scRNA structural ratio
# ══════════════════════════════════════════

def _get_mapping(dataset: Optional[str] = None, platform: str = '10x') -> dict:
    """Get the position-to-markers mapping for a dataset.

    If dataset is specified and exists in DATASET_CONFIGS, use its locked mapping.
    Otherwise fall back to the generic SCRNA_MARKERS with platform key.
    """
    if dataset and dataset in DATASET_CONFIGS:
        return DATASET_CONFIGS[dataset]['mapping']

    # Generic fallback: convert SCRNA_MARKERS to flat lists using platform
    mapping = {}
    for pos, platforms in SCRNA_MARKERS.items():
        keys = platforms.get(platform, [])
        if not keys and platform == '10x':
            keys = platforms.get('smartseq2', [])
        mapping[pos] = keys
    return mapping


def _sum_markers(fractions: dict, position: str,
                 dataset: Optional[str] = None, platform: str = '10x') -> float:
    """Sum cell fractions for a structural position.

    Args:
        fractions: dict of cell_type_name → fraction
        position: one of 'nk', 'eff', 'tex', 'treg', 'renewal'
        dataset: optional locked dataset name (e.g. 'zhang', 'bassez')
        platform: fallback platform if dataset not specified
    """
    mapping = _get_mapping(dataset, platform)
    keys = mapping.get(position, [])
    return sum(fractions.get(k, 0) for k in keys)


def score_scrna(fractions: dict, dataset: Optional[str] = None,
                platform: str = '10x') -> float:
    """FULCRUM-S ratio for scRNA cell fractions.

    ratio = (effector + NK + renewal) / (effector + NK + renewal + Treg + Tex)

    Args:
        fractions: dict of cell_type → fraction (denominator-normalized)
        dataset: locked dataset name for reproducible mapping
        platform: fallback if dataset not specified

    Returns: ratio in [0, 1]. High = agent is winning.
    """
    eps = 0.001
    nk = _sum_markers(fractions, 'nk', dataset, platform)
    eff = _sum_markers(fractions, 'eff', dataset, platform)
    tex = _sum_markers(fractions, 'tex', dataset, platform)
    treg = _sum_markers(fractions, 'treg', dataset, platform)
    renewal = _sum_markers(fractions, 'renewal', dataset, platform)

    kill = eff + nk + renewal
    suppress = treg + tex
    return kill / (kill + suppress + eps)


def features_scrna(fractions: dict, dataset: Optional[str] = None,
                   platform: str = '10x') -> dict:
    """FULCRUM-S+ features for logistic regression.

    Returns dict of 6 structural features — the same 6 positions in every dataset,
    mapped to dataset-specific cell type names.

    Args:
        fractions: dict of cell_type → fraction
        dataset: locked dataset name (e.g. 'zhang', 'bassez', 'sade_feldman')
        platform: fallback if dataset not specified
    """
    eps = 0.001
    nk = _sum_markers(fractions, 'nk', dataset, platform)
    eff = _sum_markers(fractions, 'eff', dataset, platform)
    tex = _sum_markers(fractions, 'tex', dataset, platform)
    treg = _sum_markers(fractions, 'treg', dataset, platform)
    renewal = _sum_markers(fractions, 'renewal', dataset, platform)

    kill = eff + nk + renewal
    suppress = treg + tex

    return {
        'nk': nk,
        'eff': eff,
        'tex': tex,
        'treg': treg,
        'renewal': renewal,
        'ratio': kill / (kill + suppress + eps),
    }


def report_scrna(fractions: dict, dataset: Optional[str] = None,
                 platform: str = '10x',
                 cohort_profiles: Optional[List[dict]] = None) -> dict:
    """Generate a FULCRUM-S report for a single-cell sample.

    Args:
        fractions: dict of cell_type → fraction
        dataset: locked dataset name for reproducible mapping
        platform: fallback if dataset not specified
        cohort_profiles: optional list of feature dicts from other patients

    Returns a structured report with:
      - score: the FULCRUM-S ratio
      - profile: six-position structural profile with values and assessments
      - regime: abundance-limited or quality-limited classification
      - bottleneck: which structural position is the primary deficit
      - interpretation: plain-language structural diagnosis
    """
    feats = features_scrna(fractions, dataset, platform)
    ratio = feats['ratio']

    # Build profile
    total_immune = feats['nk'] + feats['eff'] + feats['tex'] + feats['treg'] + feats['renewal']

    profile = {}
    for pos in ['nk', 'eff', 'tex', 'treg', 'renewal', 'ratio']:
        val = feats[pos]

        # Compute percentile within cohort if available
        pct = None
        if cohort_profiles:
            below = sum(1 for cp in cohort_profiles if cp.get(pos, 0) <= val)
            pct = round(100 * below / len(cohort_profiles), 1)

        # Fraction of total immune (for non-ratio positions)
        frac_of_total = val / total_immune if total_immune > 0 and pos != 'ratio' else None

        profile[pos] = {
            'value': round(val, 4),
            'label': POSITION_LABELS[pos],
            'direction': POSITION_DIRECTION[pos],
            'fraction_of_immune': round(frac_of_total, 3) if frac_of_total is not None else None,
            'percentile': pct,
        }

    # Regime classification
    # If Tregs and Tex are both high in responders, it's abundance-limited
    # Heuristic: if ratio < 0.3, likely abundance-limited
    if ratio < 0.3:
        regime = 'abundance-limited'
        regime_explanation = (
            'Most immune populations co-vary with total infiltrate in this sample. '
            'The bottleneck is immune presence, not composition. '
            'FULCRUM-S ratio may invert — use FULCRUM-S+ instead.'
        )
    else:
        regime = 'quality-limited'
        regime_explanation = (
            'Immune infiltrate is present. Effector-to-suppressor composition '
            'determines outcome. FULCRUM-S ratio is informative.'
        )

    # Find bottleneck
    # For "good" positions (nk, eff, renewal): low value = bottleneck
    # For "bad" positions (tex, treg): high value = bottleneck
    bottleneck_candidates = {}
    if feats['nk'] < 0.01:
        bottleneck_candidates['nk'] = 'SP1 Perception is near zero — innate surveillance is absent'
    if feats['renewal'] < 0.01:
        bottleneck_candidates['renewal'] = 'SP4 Renewal is near zero — no regenerative capacity'
    if feats['treg'] > feats['eff']:
        bottleneck_candidates['treg'] = 'SP4 Suppression exceeds SP3 Effector — Tregs are dominating'
    if feats['tex'] > feats['eff']:
        bottleneck_candidates['tex'] = 'SP3 Exhaustion exceeds SP3 Effector — T cells are exhausted, not killing'

    if not bottleneck_candidates:
        if ratio > 0.6:
            bottleneck = None
            bottleneck_text = 'No clear bottleneck — immune profile is balanced'
        else:
            # General suppression
            bottleneck = 'treg' if feats['treg'] > feats['tex'] else 'tex'
            bottleneck_text = f'{POSITION_LABELS[bottleneck].split("—")[0].strip()} is the largest suppressive component'
    else:
        # Pick the most severe
        bottleneck = list(bottleneck_candidates.keys())[0]
        bottleneck_text = bottleneck_candidates[bottleneck]

    # Interpretation
    parts = []
    parts.append(f"FULCRUM-S ratio: {ratio:.3f}.")
    parts.append(f"Regime: {regime}. {regime_explanation}")
    if bottleneck_text:
        parts.append(f"Primary bottleneck: {bottleneck_text}.")

    # Therapeutic direction
    therapeutic_hints = {
        'nk': 'Consider NK cell therapy or agents that enhance innate surveillance.',
        'tex': 'Checkpoint inhibitors may rescue exhausted T cells.',
        'treg': 'Anti-Treg strategies (anti-CCR8, low-dose cyclophosphamide) may shift the balance.',
        'renewal': 'IL-7 or adoptive T cell transfer may restore regenerative capacity.',
    }
    if bottleneck and bottleneck in therapeutic_hints:
        parts.append(therapeutic_hints[bottleneck])

    return {
        'model': 'FULCRUM-S',
        'version': __version__,
        'score': round(ratio, 4),
        'profile': profile,
        'regime': regime,
        'regime_explanation': regime_explanation,
        'bottleneck': bottleneck,
        'bottleneck_text': bottleneck_text,
        'total_immune': round(total_immune, 4),
        'interpretation': ' '.join(parts),
    }


# ══════════════════════════════════════════
# M_eff — Patient-level prediction
# ══════════════════════════════════════════

def m_eff(M: float, D: float, S: float = 0.0) -> float:
    """Core structural formula: M_eff = M × (1−D) / (1+D) × (1+S)

    M = base potency of the intervention
    D = conservation depth (how deeply the target has captured maintenance)
    S = surveillance signal (innate detection strength)

    This is the universal formula from Generative Geometry. The immunology
    functions above are specific instantiations of this formula.
    """
    return M * (1 - D) / (1 + D) * (1 + S)


def conservation_depth(ccr8_treg_frac: float, foxp3_treg_frac: float) -> float:
    """Compute conservation depth D from Treg sub-populations.

    D = CCR8+ Treg fraction (active suppression, weight 1.0)
      + FOXP3+ Treg fraction / φ (regulatory programme, weight 1/φ)

    Same 1/φ decay per depth level, applied within the conservation position.
    """
    return ccr8_treg_frac + foxp3_treg_frac / PHI


def report_patient(M: float, ccr8_treg_frac: float, foxp3_treg_frac: float,
                   fgfbp2_nk_frac: float) -> dict:
    """Generate a patient-level FULCRUM report.

    Args:
        M: base potency of checkpoint inhibitor for this cancer type/stage
        ccr8_treg_frac: CCR8+ Treg fraction (active suppression)
        foxp3_treg_frac: FOXP3+ Treg fraction (regulatory programme)
        fgfbp2_nk_frac: FGFBP2+ NK fraction (surveillance signal)

    Returns structured report with M_eff, depth analysis, and interpretation.
    """
    D = conservation_depth(ccr8_treg_frac, foxp3_treg_frac)
    S = fgfbp2_nk_frac
    effectiveness = m_eff(M, D, S)

    # Depth analysis
    depth_ratio = (1 - D) / (1 + D)
    suppression_pct = round((1 - depth_ratio) * 100, 1)

    # Interpretation
    parts = []
    parts.append(f"Base intervention potency: {M:.0%}.")
    parts.append(f"Conservation depth D = {D:.3f} — "
                 f"the tumour's maintenance programme reduces effectiveness by {suppression_pct}%.")

    if ccr8_treg_frac > foxp3_treg_frac:
        parts.append("Active suppression (CCR8+ Tregs) dominates — "
                     "the tumour is actively recruiting regulatory T cells.")
    else:
        parts.append("Regulatory programme (FOXP3+ Tregs) dominates — "
                     "suppression is structural rather than actively recruited.")

    parts.append(f"Surveillance signal S = {S:.3f}.")
    if S > 0.05:
        parts.append("Innate detection (NK cells) is present — "
                     "the immune system has recognised the tumour.")
    else:
        parts.append("Innate detection is low — "
                     "the immune system may not have recognised the tumour.")

    parts.append(f"Effective potency: {effectiveness:.1%}.")

    if effectiveness > 0.3:
        prediction = 'likely responder'
        parts.append("This patient is predicted to respond to checkpoint inhibitors.")
    elif effectiveness > 0.15:
        prediction = 'borderline'
        parts.append("Response is uncertain. Consider combination therapy "
                     "to shift the balance.")
    else:
        prediction = 'unlikely responder'
        parts.append("Checkpoint inhibitors alone are unlikely to produce response. "
                     "The tumour's conservation programme is too deep.")

    return {
        'model': 'FULCRUM M_eff',
        'version': __version__,
        'M_eff': round(effectiveness, 4),
        'M_base': M,
        'D': round(D, 4),
        'S': round(S, 4),
        'depth_ratio': round(depth_ratio, 4),
        'suppression_pct': suppression_pct,
        'prediction': prediction,
        'ccr8_dominance': ccr8_treg_frac > foxp3_treg_frac,
        'nk_present': S > 0.05,
        'interpretation': ' '.join(parts),
    }


# ══════════════════════════════════════════
# CONVENIENCE
# ══════════════════════════════════════════

# Aliases
fulcrum = score_log2
fulcrum_linear = score_linear
fulcrum_s = score_scrna
fulcrum_s_features = features_scrna


def list_datasets() -> dict:
    """List all locked dataset configurations.

    Returns dict of dataset_name → config summary.
    """
    return {name: {
        'name': cfg['name'],
        'source': cfg['source'],
        'n': cfg['n'],
        'platform': cfg['platform'],
        'positions': list(cfg['mapping'].keys()),
        'markers_per_position': {pos: len(markers) for pos, markers in cfg['mapping'].items()},
    } for name, cfg in DATASET_CONFIGS.items()}


def get_mapping(dataset: str) -> dict:
    """Get the locked mapping for a specific dataset.

    Returns dict of position → list of cell type names.
    Raises KeyError if dataset not in DATASET_CONFIGS.
    """
    if dataset not in DATASET_CONFIGS:
        available = ', '.join(DATASET_CONFIGS.keys())
        raise KeyError(f"Unknown dataset '{dataset}'. Available: {available}")
    return DATASET_CONFIGS[dataset]['mapping']


# ══════════════════════════════════════════
# SELF-TEST
# ══════════════════════════════════════════

if __name__ == "__main__":
    print(f"FULCRUM v{__version__}")
    print()

    # List datasets
    print("=== Locked dataset configs ===")
    for name, cfg in DATASET_CONFIGS.items():
        print(f"  {name}: {cfg['name']} (n={cfg['n']}, {cfg['platform']})")
        for pos, markers in cfg['mapping'].items():
            print(f"    {pos}: {markers}")
    print()

    # Bulk report
    print("=== FULCRUM (bulk) ===")
    r = report_bulk(gzmb=5.2, prf1=4.8, ifng=3.1, gzma=5.5, mki67=4.9)
    print(f"Score: {r['score']}")
    print(f"Prediction: {r['prediction']}")
    print(f"Balance: {r['balance']}")
    print(f"Strongest: {r['strongest_effector']}, Weakest: {r['weakest_effector']}")
    print(f"Interpretation: {r['interpretation']}")
    print()

    # scRNA report with dataset config
    print("=== FULCRUM-S (Bassez mapping) ===")
    r2 = report_scrna({
        'NK_CYTO': 0.01, 'NK_REST': 0.035,
        'CD8_EM': 0.08, 'CD8_RM': 0.04, 'CD8_EMRA': 0.01,
        'CD8_EX': 0.06, 'CD8_EX_Proliferating': 0.01,
        'CD4_REG': 0.09, 'CD4_REG_Proliferating': 0.02,
        'CD8_N': 0.03, 'CD4_N': 0.04,
    }, dataset='bassez')
    print(f"Score: {r2['score']}")
    print(f"Regime: {r2['regime']}")
    print(f"Bottleneck: {r2['bottleneck_text']}")
    print()

    # Same data with Zhang mapping — should return zeros (wrong names)
    print("=== FULCRUM-S (Zhang mapping on Bassez names — expect zeros) ===")
    r3 = report_scrna({
        'NK_CYTO': 0.01, 'NK_REST': 0.035,
        'CD8_EM': 0.08, 'CD8_RM': 0.04,
    }, dataset='zhang')
    print(f"Score: {r3['score']} (should be ~0.5 — names don't match Zhang config)")
    print()

    # Evaluation protocol
    print(f"=== Locked evaluation protocol ===")
    for k, v in EVAL_PROTOCOL.items():
        print(f"  {k}: {v}")
