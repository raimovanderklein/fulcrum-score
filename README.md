# FULCRUM

**The first immunotherapy prediction framework derived from structural theory.**

FULCRUM measures the balance between two competing dissipative systems — the immune response and the tumour. It predicts immunotherapy response and explains why, returning a structural diagnosis rather than just a score.

→ **[Full documentation at generativegeometry.science/fulcrum](https://www.generativegeometry.science/fulcrum)**

## Quick start

```python
from fulcrum import report_bulk

# Score a patient from bulk gene expression (log2 TPM+1)
report = report_bulk(gzmb=5.2, prf1=4.8, ifng=3.1, gzma=5.5, mki67=4.9)

print(report['score'])           # 13.7
print(report['prediction'])      # 'likely responder'
print(report['balance'])         # 'immune system is outpacing the tumour'
print(report['weakest_effector']) # 'IFNG'
print(report['interpretation'])  # Full plain-language report
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

### Pan-cancer survival (TCGA, n=9,966, 33 cancer types)
FULCRUM HR = 0.935, p = 0.0002. The only immune score significantly protective pan-cancer. CYT, IFN-γ, and GEP all fail.

### Immunotherapy response (13 datasets, ~1,400 patients)
Correct direction (hi = respond) on 12/13 ICI datasets across 6 cancer types.

### Single-cell head-to-head (3 datasets, 290 patients)
| Dataset | FULCRUM-S+ (6 feat) | Full ML | Full ML features |
|---------|--------------------:|--------:|-----------------:|
| Zhang NSCLC (n=242) | 0.770 | 0.762 | 51 |
| Sade-Feldman Melanoma (n=19) | 0.889 | 0.922 | 30 |
| Bassez Breast (n=29) | 0.922 | 0.843 | 16 |

Same patients, same folds, same seed. Protocol: repeated stratified 5-fold CV, 200 repeats, seed=42, C=1.0.

### Patient-level (no ML)
Zhang NSCLC AUC 0.808 (vs oncologist 0.72, PD-L1 0.64).

## Repository structure

```
fulcrum.py                          # The package — all formulas + report functions
FULCRUM_REPRODUCIBILITY_SPEC.md     # Locked protocol for all reported results
data/
  bassez_cell_fractions.json        # Processed Bassez fractions (n=29)
  zhang_cell_fractions_fulcrum.json  # Processed Zhang fractions (n=242)
notebooks/                          # Jupyter notebooks reproducing all results
```

## The formula

The core structural formula from Generative Geometry:

```
M_eff = M × (1−D) / (1+D)
```

Applied to immunology:

```
score = log₂(GZMB) + log₂(PRF1) + log₂(IFNG) + log₂(GZMA) − log₂(MKI67)
```

Immune kill rate divided by tumour growth rate. The ratio of two dissipative systems.

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
FULCRUM-S Scorer (fulcrum_s_scorer.py)
Patient-level immunotherapy response prediction from scRNA-seq data.
What it does
Takes any h5ad file with cell type annotations and patient response labels, maps cell types to FULCRUM structural positions, and computes M_eff = (1−D)/(1+D) × (1+S) per patient — where D is the drain (Treg + exhausted CD8 fraction) and S is the surveillance signal (NK fraction). Two measurements per patient, zero machine learning, zero fitted parameters.
Also classifies each patient's regime (quality-limited vs abundance-limited) and reports AUC overall and by regime.
Quick start
bashpip install scanpy   # or: pip install h5py pandas numpy

# Auto-detect columns:
python fulcrum_s_scorer.py my_dataset.h5ad

# Specify columns:
python fulcrum_s_scorer.py my_dataset.h5ad \
    --patient donor_id --celltype cell_type --response outcome

# Include post-treatment samples:
python fulcrum_s_scorer.py my_dataset.h5ad --all-timepoints

# Custom output:
python fulcrum_s_scorer.py my_dataset.h5ad -o results.csv
Using with the Gondal integrated ICB database
The integrated ICB scRNA-seq dataset (Gondal et al., Scientific Data 2025) covers 9 cancer types and 223 patients with cell type annotations and ICB response labels.
bash# Download (~3 GB):
wget "https://datasets.cellxgene.cziscience.com/134d34af-cbcd-4837-9310-3d1f83ec6f18.h5ad" \
    -O gondal_icb.h5ad

# Score all cancer types:
python fulcrum_s_scorer.py gondal_icb.h5ad -o gondal_results.csv
Cell type mapping
The scorer maps ~60 common annotation labels to five structural positions:
PositionRoleExample labelsNKDetection/surveillanceNK cell, Natural Killer, NKTCD8_effectorKill capacityCD8_Teff, Cytotoxic T, CD8_GZMB+CD8_exhaustedEncounter drainCD8_Tex, dysfunctional CD8, CD8_HAVCR2+TregSuppressive drainTreg, regulatory T, FOXP3+CD8_memoryRenewal capacityCD8_Tcm, stem-like CD8, CD8_TCF7+
Unmapped cell types are reported. To add custom mappings, edit the STRUCTURAL_POSITIONS dictionary.
Validated results
DatasetCancernAUCComparisonZhang 2025NSCLC1590.808Oncologist: 0.72, PD-L1: 0.64Sade-Feldman 2018Melanoma190.889—Yost 2019BCC110.767—Bassez 2021Breast290.922Full ML (16 feat): 0.843

## Status

FULCRUM is pre-publication. The paper is in preparation. All code, data, and results are openly available for independent verification.

## License

MIT

## Author

Raimo van der Klein · [generativegeometry.science](https://www.generativegeometry.science)
