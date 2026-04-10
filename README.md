# FULCRUM

**The first immunotherapy prediction framework derived from structural theory.**

FULCRUM measures the balance between two competing dissipative systems — the immune response and the tumour. It predicts immunotherapy response and explains why, returning a structural diagnosis rather than just a score.

→ **[Full documentation at generativegeometry.science/fulcrum](https://www.generativegeometry.science/fulcrum)**

## Quick start

```python
from fulcrum import report_bulk

# Score a patient from bulk gene expression (log2 TPM+1)
report = report_bulk(gzmb=5.2, prf1=4.8, ifng=3.1, gzma=5.5, mki67=4.9)

print(report['score'])            # 13.7
print(report['prediction'])       # 'likely responder'
print(report['balance'])          # 'immune system is outpacing the tumour'
print(report['weakest_effector']) # 'IFNG'
print(report['interpretation'])   # Full plain-language report
```

## Three models

| Model | Input | ML required | Use when |
|-------|-------|-------------|----------|
| **FULCRUM** | 5 bulk genes | None | You have RNA-seq, NanoString, or microarray |
| **FULCRUM-S** | scRNA cell fractions | None | Quality-limited cancers (NSCLC, melanoma) |
| **FULCRUM-S+** | scRNA cell fractions | Logistic regression | Any cancer including abundance-limited |

## What makes it different

- **Zero fitted parameters** in the base formula — derived from structural theory, not trained on data
- **Returns a diagnosis**, not just a number — effector profile, tumour aggression, balance, bottleneck identification, regime classification
- **6 structural features match 51-feature ML** across three cancer types
- **Regime diagnosis** — explains *why* a biomarker fails in a specific cancer type
- **Beats state-of-the-art benchmarks** on their own data with 5 genes and no training

## The formula

The core structural formula from Generative Geometry:

```
M_eff = M × (1−D) / (1+D)
```

Applied to bulk immunology:

```
score = log₂(GZMB) + log₂(PRF1) + log₂(IFNG) + log₂(GZMA) − log₂(MKI67)
```

Immune kill rate divided by tumour growth rate. The ratio of two dissipative systems.

Applied at single-cell resolution (FULCRUM-S):

```
M_eff = (1−D) / (1+D) × (1+S)
```

where D = Treg + exhausted CD8 fraction (drain) and S = NK fraction (surveillance). Two patient measurements. Zero machine learning.

## Report functions

Every function returns a structured dict with an `interpretation` field:

```python
from fulcrum import report_bulk, report_scrna, report_patient

# Bulk expression
r = report_bulk(gzmb=5.2, prf1=4.8, ifng=3.1, gzma=5.5, mki67=4.9)

# scRNA with dataset-locked mapping
r = report_scrna(cell_fractions, dataset='bassez')
# → score, profile, regime, bottleneck, therapeutic direction

# Patient-level (two measurements, no ML)
r = report_patient(M=0.45, ccr8_treg_frac=0.08,
                   foxp3_treg_frac=0.12, fgfbp2_nk_frac=0.03)
```

## Dataset-locked mappings

Each validated dataset has a locked mapping from cell type names to FULCRUM structural positions:

```python
from fulcrum import list_datasets, get_mapping

list_datasets()
# → {'zhang': {...}, 'bassez': {...}, 'sade_feldman': {...}}

get_mapping('bassez')
# → {'nk': ['NK_CYTO', 'NK_REST'], 'eff': ['CD8_EM', ...], ...}
```

Using `dataset='bassez'` ensures reproducible results. See `FULCRUM_REPRODUCIBILITY_SPEC.md` for the complete protocol.

## Validated results

### Head-to-head against state of the art (bulk)

FULCRUM has been compared against the two largest transcriptomic ICI prediction frameworks on their own data:

| Comparison | Cohorts | FULCRUM | Benchmark | FULCRUM genes | Benchmark genes |
|------------|---------|---------|-----------|---------------|-----------------|
| vs EXPRESSO-B (melanoma) | 8 | 0.710 | 0.710 | 5 | whole transcriptome |
| vs EXPRESSO-T (non-melanoma) | 7 | 0.768 | 0.720 | 5 | whole transcriptome |
| vs TIME_ACT (shared cohorts) | 8 | 0.825 | 0.794 | 5 | 66 |

EXPRESSO: Pal, Ruppin et al. (2025). bioRxiv 10.1101/2025.10.24.684491v2. Supervised LASSO trained on 69 cohorts, 3,729 patients.
TIME_ACT: Mukherjee, Ruppin et al. (2025). bioRxiv 10.1101/2025.06.27.661875v2. Unsupervised 66-gene signature.

### Pan-cancer survival (TCGA, n=9,966, 33 cancer types)

FULCRUM HR = 0.935, p = 0.0002. The only immune score significantly protective pan-cancer. CYT, IFN-γ, and GEP all fail (all p > 0.1). Removing the MKI67 denominator renders the same four genes non-significant (p = 0.402).

### Immunotherapy response (13 datasets, ~1,400 patients)

Correct direction (high score = respond) on 12/13 ICI datasets across 6 cancer types. AUC range 0.530–0.847.

### Single-cell head-to-head (3 datasets, 290 patients)

| Dataset | FULCRUM-S+ v1 (6 feat) | FULCRUM-S+ v2 (7 feat) | Full ML | Full ML features |
|---------|------------------------|------------------------|---------|------------------|
| Zhang NSCLC (n=242) | 0.781 | **0.808** | 0.746 | 51 |
| Sade-Feldman Melanoma (n=19) | 0.918 | **0.941** | 0.933 | 30 |
| Bassez Breast (n=29) | 0.856 | — (abundance-limited) | 0.843 | 16 |

Same patients, same folds, same seed. Protocol: repeated stratified 5-fold CV, 200 repeats, seed=42, C=1.0.

v2 adds one structural feature: host Conservation drain (inflammatory macrophages at the encounter site). See changelog below.

### Patient-level prediction (no ML)

| Dataset | Cancer | n | AUC | Comparison |
|---------|--------|---|-----|------------|
| Zhang 2025 | NSCLC | 159 | 0.808 | Oncologist: 0.72, PD-L1: 0.64 |
| Sade-Feldman 2018 | Melanoma | 19 | 0.889 | — |
| Yost 2019 | BCC | 11 | 0.767 | — |

Two cell-type measurements per patient. Zero machine learning.

### External validation (new in v0.15.0)

| Dataset | Cancer | n | FULCRUM v1 AUC | Platform |
|---------|--------|---|----------------|----------|
| GSE207422 | NSCLC | 24 | 0.822 | Bulk RNA-seq |

Independent NSCLC cohort. No training. Five genes.

---

## v0.15.0 — Host Conservation drain (FULCRUM-S v2)

The patient's body is a dissipative system hosting the immune-tumour encounter. Its maintenance programme — specifically inflammatory macrophages at the tumour site — interferes with the immune response by competing for tissue space.

### The formula change

```
v1: ratio = kill / (kill + suppress + ε)
v2: ratio = kill / (kill + suppress + host_drain + ε)
```

One additional term. Same formula shape. Zero additional fitted parameters.

`host_drain` = inflammatory macrophage fraction: CXCL10, DNAJB1, ISG15, MKI67 macrophage subtypes on scRNA. Only inflammatory subtypes contribute — tissue-resident (FOLR2, MARCO) and scavenging macrophages hurt performance.

### v2 results across cancer types (scRNA)

| Dataset | n | Cancer | v1 | v2 | Δ |
|---------|---|--------|-----|-----|---|
| Zhang NSCLC (10x) | 242 | NSCLC | 0.781 | **0.808** | +0.027 |
| Sade-Feldman (SS2) | 19 | Melanoma | 0.918 | **0.941** | +0.022 |
| Yost BCC (10x) | 11 | BCC | 0.600 | 0.633 | +0.033 |
| CRC GSE236581 (10x) | 22 | Colorectal | 0.442 | 0.483 | +0.042 |

Direction: v2 ≥ v1 on **all four cancer types**. Bootstrap P(v2 > v1) = 94.6% on Zhang.

### Controls

- **All macrophages** (not just inflammatory): Zhang 0.780 → 0.740 (−0.040). Only inflammatory subtypes work.
- **Bulk RNA**: IMvigor210 (−0.012), TCGA (−0.037), GSE207422 (−0.037). Host drain genes are too broadly expressed without cell-type resolution.
- **Abundance-limited** (Bassez breast, coarse myeloid): v2 partially fixes inversion but hurts FULCRUM-S+ ML (−0.065). Requires inflammatory mac subtypes, not coarse myeloid labels.

### Usage

```python
# v2 scoring (scRNA with inflammatory macrophage annotations)
score = score_scrna(cell_fractions, dataset='zhang', include_host_drain=True)
features = features_scrna(cell_fractions, dataset='zhang', include_host_drain=True)

# Patient-level with host drain
report = report_patient(M=0.45, ccr8_treg_frac=0.08,
                        foxp3_treg_frac=0.12, fgfbp2_nk_frac=0.03,
                        host_drain_frac=0.05)
```

Use `include_host_drain=True` only when inflammatory macrophage subtypes are available in the cell type annotations. Default is `False` (v1 behaviour).

## FULCRUM-S Scorer (`fulcrum_s_scorer.py`)

Standalone command-line tool for scoring any h5ad file with cell type annotations and patient response labels.

### Quick start

```bash
pip install scanpy   # or: pip install h5py pandas numpy

# Auto-detect columns:
python fulcrum_s_scorer.py my_dataset.h5ad

# Specify columns:
python fulcrum_s_scorer.py my_dataset.h5ad \
    --patient donor_id --celltype cell_type --response outcome

# Include post-treatment samples:
python fulcrum_s_scorer.py my_dataset.h5ad --all-timepoints

# Custom output:
python fulcrum_s_scorer.py my_dataset.h5ad -o results.csv
```

### Using with the Gondal integrated ICB database

The [integrated ICB scRNA-seq dataset](https://cellxgene.cziscience.com/collections/61e422dd-c9cd-460e-9b91-72d9517348ef) (Gondal et al., Scientific Data 2025) covers 9 cancer types and 223 patients.

```bash
# Download (~3 GB):
wget "https://datasets.cellxgene.cziscience.com/134d34af-cbcd-4837-9310-3d1f83ec6f18.h5ad" \
    -O gondal_icb.h5ad

# Score all cancer types:
python fulcrum_s_scorer.py gondal_icb.h5ad -o gondal_results.csv
```

### Cell type mapping

The scorer maps ~60 common annotation labels to five structural positions:

| Position | Role | Example labels |
|----------|------|---------------|
| NK | Detection/surveillance | NK cell, Natural Killer, NKT |
| CD8_effector | Kill capacity | CD8_Teff, Cytotoxic T, CD8_GZMB+ |
| CD8_exhausted | Encounter drain | CD8_Tex, dysfunctional CD8, CD8_HAVCR2+ |
| Treg | Suppressive drain | Treg, regulatory T, FOXP3+ |
| CD8_memory | Renewal capacity | CD8_Tcm, stem-like CD8, CD8_TCF7+ |

Unmapped cell types are reported. To add custom mappings, edit the `STRUCTURAL_POSITIONS` dictionary in `fulcrum_s_scorer.py`.

## Repository structure

```
fulcrum.py                          # The package — all formulas + report functions
fulcrum_s_scorer.py                 # CLI tool for scoring h5ad files
FULCRUM_REPRODUCIBILITY_SPEC.md     # Locked protocol for all reported results
bassez_cell_fractions.json          # Processed Bassez fractions (n=29)
sade_feldman_cell_fractions.json    # Processed Sade-Feldman fractions (n=19)
zhang_cell_fractions.json           # Zhang patient metadata (n=243)
notebooks/                          # Jupyter notebooks reproducing all results
```

## Citation

```bibtex
@article{vanderklein2026fulcrum,
  author = {van der Klein, Raimo},
  title  = {FULCRUM: Predicting immunotherapy response from the
            structural theory of dissipative systems},
  year   = {2026},
  doi    = {10.5281/zenodo.19399587},
  url    = {https://www.generativegeometry.science/fulcrum}
}
```

## References

- FULCRUM paper: van der Klein R (2026). Zenodo [10.5281/zenodo.19399587](https://doi.org/10.5281/zenodo.19399587)
- Generative Geometry: van der Klein R (2026). [generativegeometry.science](https://www.generativegeometry.science)
- EXPRESSO: Pal, Ruppin et al. (2025). bioRxiv [10.1101/2025.10.24.684491v2](https://doi.org/10.1101/2025.10.24.684491v2)
- TIME_ACT: Mukherjee, Ruppin et al. (2025). bioRxiv [10.1101/2025.06.27.661875v2](https://doi.org/10.1101/2025.06.27.661875v2)
- Zhang NSCLC: Liu, Yang et al. (2025). Cell 188:3081–3096
- Thorsson immune landscape: Thorsson et al. (2018). Immunity 48:812–830

## Status

FULCRUM is pre-publication. The paper is in preparation. All code, data, and results are openly available for independent verification.

## License

All Rights Reserved. © 2026 Raimo van der Klein.

## Author

Raimo van der Klein · [generativegeometry.science](https://www.generativegeometry.science) · raimo@generativegeometry.science
