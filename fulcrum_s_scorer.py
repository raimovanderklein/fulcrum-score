#!/usr/bin/env python3
"""
FULCRUM-S Scorer
================
Patient-level immunotherapy response prediction from scRNA-seq cell type fractions.

Usage:
    python fulcrum_s_scorer.py <input.h5ad> [--output results.csv]
    python fulcrum_s_scorer.py <input.h5ad> --patient donor_id --celltype cell_type --response outcome

Theory:
    M_eff = M × (1−D)/(1+D) × (1+S)

    D = conservation depth (drain): suppressive/exhausted cell fraction
    S = surveillance signal (renewal): NK / memory cell fraction
    M = 1 (base potency, constant for scoring)

    Two patient measurements. Zero machine learning. Zero fitted parameters.

Reference:
    van der Klein R (2026). FULCRUM: Predicting Immunotherapy Response from the
    Structural Theory of Dissipative Systems. Zenodo 10.5281/zenodo.19399587
    Generative Geometry (van der Klein, 2026). https://www.generativegeometry.science
"""

import argparse
import sys
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import product as iterproduct

warnings.filterwarnings('ignore')


# ═══════════════════════════════════════════════════════════════════
# CELL TYPE MAPPING — common annotation labels → structural positions
# ═══════════════════════════════════════════════════════════════════

STRUCTURAL_POSITIONS = {
    'NK': [
        'NK', 'NK cell', 'NK cells', 'NK_cell', 'NKcell',
        'Natural Killer', 'natural killer cell',
        'NK cell_CD56bright', 'NK cell_CD56dim',
        'NK_CD56bright', 'NK_CD56dim', 'KLRB1+ NK', 'NKT', 'NK/NKT',
    ],
    'CD8_effector': [
        'CD8_eff', 'CD8_Eff', 'CD8 Eff', 'CD8_effector', 'CD8 effector',
        'Effector CD8', 'CD8+ effector', 'CD8_Teff', 'CD8-Teff',
        'Cytotoxic T', 'cytotoxic T cell', 'CTL',
        'CD8+ T cell', 'CD8_T', 'CD8 T cell', 'CD8+ T',
        'CD8_GZMB+', 'CD8_GZMK+', 'CD8_effector_memory', 'CD8_em',
        'T cell CD8+', 'T cell_CD8_effector', 'activated CD8 T',
    ],
    'CD8_exhausted': [
        'CD8_ex', 'CD8_Ex', 'CD8 Ex', 'CD8_exhausted', 'CD8 exhausted',
        'Exhausted CD8', 'CD8+ exhausted', 'CD8_Tex', 'CD8-Tex',
        'dysfunctional CD8', 'CD8_dysfunction',
        'CD8_HAVCR2+', 'CD8_LAG3+', 'CD8_PDCD1+',
        'CD8_terminal_exhaustion', 'T cell_CD8_exhausted',
        'terminally exhausted CD8',
    ],
    'Treg': [
        'Treg', 'Tregs', 'T_reg', 'T reg', 'regulatory T',
        'Regulatory T cell', 'CD4_Treg', 'CD4+ Treg', 'FOXP3+',
        'T cell_Treg', 'T cell_regulatory', 'Treg_FOXP3',
        'CCR8+ Treg', 'activated Treg', 'resting Treg',
    ],
    'CD8_memory': [
        'CD8_mem', 'CD8_Mem', 'CD8 memory', 'CD8_memory',
        'Memory CD8', 'CD8+ memory', 'CD8_Tcm', 'CD8_Trm',
        'CD8_naive', 'CD8 naive', 'Naive CD8', 'CD8_stem',
        'CD8_TCF7+', 'CD8_progenitor', 'stem-like CD8',
        'T cell_CD8_memory', 'T cell_CD8_naive',
        'tissue-resident memory CD8', 'CD8_TRM',
    ],
}

LABEL_TO_POSITION = {}
for pos, labels in STRUCTURAL_POSITIONS.items():
    for label in labels:
        LABEL_TO_POSITION[label.lower().strip()] = pos


RESPONDER_LABELS = {
    'r', 'responder', 'response', 'cr', 'pr', 'complete response',
    'partial response', 'high', 'dcb', 'durable clinical benefit',
    'favorable', 'favourable', 'yes', 'true', '1',
}

NON_RESPONDER_LABELS = {
    'nr', 'non-responder', 'nonresponder', 'non_responder', 'no response',
    'sd', 'pd', 'stable disease', 'progressive disease',
    'low', 'medium', 'ndb', 'no durable benefit',
    'unfavorable', 'unfavourable', 'no', 'false', '0',
    'resistant', 'resistance',
}


# ═══════════════════════════════════════════════════════════════════
# COLUMN DETECTION
# ═══════════════════════════════════════════════════════════════════

def detect_columns(obs_df, patient_col=None, celltype_col=None, response_col=None):
    """Auto-detect patient, cell type, and response columns."""
    cols_lower = {c: c.lower().replace('_', ' ').replace('-', ' ') for c in obs_df.columns}

    if patient_col is None:
        for col, cl in cols_lower.items():
            if any(kw in cl for kw in ['patient', 'donor', 'sample', 'subject', 'individual']):
                patient_col = col
                break

    if celltype_col is None:
        for col, cl in cols_lower.items():
            if any(kw in cl for kw in ['cell type', 'celltype', 'cell_type', 'annotation',
                                        'cluster', 'cell label']):
                celltype_col = col
                break

    if response_col is None:
        for col, cl in cols_lower.items():
            if any(kw in cl for kw in ['response', 'outcome', 'path response', 'clinical',
                                        'recist', 'benefit', 'responder']):
                response_col = col
                break

    return patient_col, celltype_col, response_col


def detect_timepoint_col(obs_df):
    """Detect a timepoint column to filter pre-treatment samples."""
    cols_lower = {c: c.lower().replace('_', ' ') for c in obs_df.columns}
    for col, cl in cols_lower.items():
        if any(kw in cl for kw in ['timepoint', 'time point', 'stage',
                                    'treatment', 'biopsy', 'timing']):
            return col
    return None


def is_pretreatment(value):
    v = str(value).lower().strip()
    return any(kw in v for kw in ['pre', 'baseline', 'before', 'naive',
                                   'untreated', 'screening', 'day 0', 'd0'])


# ═══════════════════════════════════════════════════════════════════
# FULCRUM-S COMPUTATION
# ═══════════════════════════════════════════════════════════════════

def map_celltypes(celltype_series):
    """Map cell type labels to structural positions. Returns (list, set of unmapped)."""
    mapped = []
    unmapped = set()
    for ct in celltype_series:
        ct_lower = str(ct).lower().strip()
        if ct_lower in LABEL_TO_POSITION:
            mapped.append(LABEL_TO_POSITION[ct_lower])
        else:
            found = False
            for label, pos in LABEL_TO_POSITION.items():
                if label in ct_lower or ct_lower in label:
                    mapped.append(pos)
                    found = True
                    break
            if not found:
                mapped.append('other')
                unmapped.add(ct)
    return mapped, unmapped


def compute_patient_fractions(obs_df, patient_col, celltype_col):
    """Per-patient cell type fractions for the five structural positions."""
    obs_df = obs_df.copy()
    mapped, unmapped = map_celltypes(obs_df[celltype_col])
    obs_df['_pos'] = mapped

    positions = ['NK', 'CD8_effector', 'CD8_exhausted', 'Treg', 'CD8_memory']
    records = []
    for patient, grp in obs_df.groupby(patient_col):
        total = len(grp)
        immune = grp[grp['_pos'] != 'other'].shape[0]
        fracs = {'patient': patient, 'total_cells': total, 'immune_cells': immune}
        for pos in positions:
            count = (grp['_pos'] == pos).sum()
            fracs[f'{pos}_count'] = count
            fracs[f'{pos}_frac'] = count / total if total > 0 else 0
            fracs[f'{pos}_immune_frac'] = count / immune if immune > 0 else 0
        records.append(fracs)
    return pd.DataFrame(records), unmapped


def score_fulcrum_s(fractions_df, d_cols=None, s_col=None):
    """
    M_eff = (1-D)/(1+D) × (1+S)

    Default D = Treg + CD8_exhausted immune fractions
    Default S = NK immune fraction
    """
    if d_cols is None:
        d_cols = ['Treg_immune_frac', 'CD8_exhausted_immune_frac']
    if s_col is None:
        s_col = 'NK_immune_frac'

    df = fractions_df.copy()
    df['D'] = df[d_cols].sum(axis=1).clip(0, 0.99)
    df['S'] = df[s_col].clip(0, None)
    df['fulcrum_s'] = (1 - df['D']) / (1 + df['D']) * (1 + df['S'])
    return df


def classify_regime(df):
    """Quality-limited vs abundance-limited based on total immune fraction."""
    cols = [c for c in df.columns if c.endswith('_frac') and not c.endswith('_immune_frac')]
    df = df.copy()
    df['immune_abundance'] = df[cols].sum(axis=1)
    median = df['immune_abundance'].median()
    df['regime'] = np.where(df['immune_abundance'] >= median,
                            'quality-limited', 'abundance-limited')
    return df


def compute_auc(r_scores, nr_scores):
    """AUC via Mann-Whitney U."""
    if not r_scores or not nr_scores:
        return None
    c = sum(1 for a, b in iterproduct(r_scores, nr_scores) if a > b)
    t = sum(0.5 for a, b in iterproduct(r_scores, nr_scores) if a == b)
    return (c + t) / (len(r_scores) * len(nr_scores))


# ═══════════════════════════════════════════════════════════════════
# PIPELINE
# ═══════════════════════════════════════════════════════════════════

def run(h5ad_path, patient_col=None, celltype_col=None,
        response_col=None, pretreatment_only=True, output_path=None):

    print(f"\n{'='*60}")
    print(f"FULCRUM-S Scorer")
    print(f"{'='*60}")
    print(f"Input: {h5ad_path}")

    # Load
    try:
        import scanpy as sc
        adata = sc.read_h5ad(h5ad_path)
        obs = adata.obs.copy()
        print(f"Loaded: {adata.n_obs:,} cells × {adata.n_vars:,} genes")
    except ImportError:
        import h5py
        print("scanpy not found, reading obs with h5py...")
        with h5py.File(h5ad_path, 'r') as f:
            obs_data = {}
            for key in f['obs'].keys():
                ds = f['obs'][key]
                if hasattr(ds, 'shape'):
                    data = ds[:]
                    if data.dtype.kind in ('O', 'S'):
                        data = [x.decode() if isinstance(x, bytes) else x for x in data]
                    obs_data[key] = data
            obs = pd.DataFrame(obs_data)
        print(f"Loaded obs: {len(obs):,} cells")

    print(f"Columns: {list(obs.columns)}")

    # Detect columns
    patient_col, celltype_col, response_col = detect_columns(
        obs, patient_col, celltype_col, response_col)
    print(f"\nPatient:   {patient_col}")
    print(f"Cell type: {celltype_col}")
    print(f"Response:  {response_col}")

    if not patient_col or not celltype_col:
        print("\nERROR: could not detect required columns.")
        print("Specify --patient and --celltype.")
        return None

    # Filter pre-treatment
    if pretreatment_only:
        tp_col = detect_timepoint_col(obs)
        if tp_col:
            mask = obs[tp_col].apply(is_pretreatment)
            if mask.sum() > 0:
                print(f"\nPre-treatment filter ({tp_col}): {mask.sum():,} / {len(obs):,} cells")
                obs = obs[mask].copy()

    # Cell types
    print(f"\nCell types ({obs[celltype_col].nunique()} unique):")
    for ct, n in obs[celltype_col].value_counts().head(15).items():
        print(f"  {ct}: {n:,}")

    # Compute
    fractions, unmapped = compute_patient_fractions(obs, patient_col, celltype_col)
    if unmapped:
        print(f"\nUnmapped cell types ({len(unmapped)}):")
        for u in sorted(unmapped)[:10]:
            print(f"  {u}")

    # Response labels
    if response_col:
        patient_resp = obs.groupby(patient_col)[response_col].first()
        fractions['response_raw'] = fractions['patient'].map(patient_resp)
        fractions['response'] = fractions['response_raw'].apply(
            lambda v: 'R' if str(v).lower().strip() in RESPONDER_LABELS
            else ('NR' if str(v).lower().strip() in NON_RESPONDER_LABELS else None))
        print(f"\nR: {(fractions['response']=='R').sum()}, "
              f"NR: {(fractions['response']=='NR').sum()}, "
              f"unmapped: {fractions['response'].isna().sum()}")

    fractions = score_fulcrum_s(fractions)
    fractions = classify_regime(fractions)

    # AUC
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")

    if response_col and 'response' in fractions.columns:
        scored = fractions.dropna(subset=['response'])
        r = scored[scored['response'] == 'R']['fulcrum_s'].tolist()
        nr = scored[scored['response'] == 'NR']['fulcrum_s'].tolist()
        auc = compute_auc(r, nr)

        if auc is not None:
            print(f"\nOverall: AUC = {auc:.3f}  ({len(r)}R / {len(nr)}NR, n={len(scored)})")

        for regime in ['quality-limited', 'abundance-limited']:
            sub = scored[scored['regime'] == regime]
            rs = sub[sub['response'] == 'R']['fulcrum_s'].tolist()
            nrs = sub[sub['response'] == 'NR']['fulcrum_s'].tolist()
            a = compute_auc(rs, nrs)
            if a is not None:
                print(f"  {regime}: AUC = {a:.3f}  ({len(rs)}R / {len(nrs)}NR)")

        # By disease/dataset if available
        for grp_col in ['dataset', 'disease', 'cancer_type', 'study']:
            if grp_col in obs.columns:
                pg = obs.groupby(patient_col)[grp_col].first()
                scored = scored.copy()
                scored['_grp'] = scored['patient'].map(pg)
                print(f"\nBy {grp_col}:")
                for g, sub in scored.groupby('_grp'):
                    rs = sub[sub['response'] == 'R']['fulcrum_s'].tolist()
                    nrs = sub[sub['response'] == 'NR']['fulcrum_s'].tolist()
                    a = compute_auc(rs, nrs)
                    if a is not None and len(rs) >= 2 and len(nrs) >= 2:
                        print(f"  {g}: AUC = {a:.3f}  ({len(rs)}R / {len(nrs)}NR)")
                break

    # Save
    if output_path is None:
        output_path = f"fulcrum_s_results_{Path(h5ad_path).stem}.csv"
    fractions.to_csv(output_path, index=False, float_format='%.6f')
    print(f"\nSaved: {output_path}")
    return fractions


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='FULCRUM-S: Structural immunotherapy response prediction from scRNA-seq')
    parser.add_argument('input', help='Path to h5ad file')
    parser.add_argument('--patient', help='Patient/donor ID column')
    parser.add_argument('--celltype', help='Cell type annotation column')
    parser.add_argument('--response', help='Response label column')
    parser.add_argument('--output', '-o', help='Output CSV path')
    parser.add_argument('--all-timepoints', action='store_true',
                        help='Use all timepoints, not just pre-treatment')
    args = parser.parse_args()

    run(h5ad_path=args.input,
        patient_col=args.patient,
        celltype_col=args.celltype,
        response_col=args.response,
        pretreatment_only=not args.all_timepoints,
        output_path=args.output)
