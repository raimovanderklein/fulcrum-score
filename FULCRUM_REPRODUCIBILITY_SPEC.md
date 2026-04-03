# FULCRUM Reproducibility Specification
## Version 14.1 · April 3, 2026

This document specifies every decision required to reproduce the results
reported on the FULCRUM page and in the forthcoming paper. If any detail
is ambiguous, this file is the authority.

---

## 1. FULCRUM (bulk gene expression)

### Formula
```
log2 platform:   score = log2(GZMB) + log2(PRF1) + log2(IFNG) + log2(GZMA) - log2(MKI67)
linear platform: score = (GZMB + PRF1 + IFNG + GZMA) / (MKI67 + 0.01)
```

### Gene identifiers
| Gene | HGNC Symbol | Ensembl | Role |
|------|-------------|---------|------|
| GZMB | GZMB | ENSG00000100453 | Effector — granzyme B |
| PRF1 | PRF1 | ENSG00000180644 | Effector — perforin |
| IFNG | IFNG | ENSG00000111537 | Effector — interferon gamma |
| GZMA | GZMA | ENSG00000145649 | Effector — granzyme A |
| MKI67 | MKI67 | ENSG00000148773 | Growth — proliferation marker |

### TCGA validation
- Source: TCGA Pan-Cancer Atlas (Thorsson et al. 2018)
- Supplementary: `curl -sL "https://ars.els-cdn.com/content/image/1-s2.0-S1074761318301213-mmc2.xlsx"`
- Gene expression: iAtlas, log2(TPM+1) harmonized
- Patients: n=9,966 (after excluding missing values)
- Cancer types: 33
- Survival: overall survival, Cox proportional hazards
- Split: median FULCRUM score within each cancer type
- Covariates: none (univariate)

---

## 2. FULCRUM-S / FULCRUM-S+ (scRNA cell fractions)

### Structural positions
| Position | Function | Direction (quality-limited) |
|----------|----------|-----------------------------|
| NK | Detection — innate surveillance | higher is better |
| Effector | Kill capacity — cytotoxic output | context-dependent |
| Exhaustion | Failed engagement — energy without output | higher is worse |
| Suppression | Conservation captured by target | higher is worse |
| Renewal | Conservation maintained by agent | higher is better |
| Ratio | (NK+eff+renewal) / (NK+eff+renewal+tex+treg+0.001) | higher is better |

### FULCRUM-S
Single feature: the ratio. No ML.

### FULCRUM-S+
Six features: NK, effector, exhaustion, suppression, renewal, ratio.
All fed into logistic regression. Same 6 features in every dataset.

---

## 3. Dataset-specific mapping tables

### Zhang et al. 2025 (NSCLC, n=242)
- Source: GSE243013
- Metadata: GSE243013_NSCLC_immune_scRNA_metadata.csv.gz
- Denominator: total immune cells per patient (all cells in metadata)
- Inclusion: exclude patients with response = "unknowm" (n=1)
- Response: MPR or pCR = responder (n=130), non-MPR = non-responder (n=112)

| Position | Zhang subtypes |
|----------|---------------|
| NK | NK_CD16hi_FGFBP2, NK_CD16low_GZMK, CD8T_NK-like_FGFBP2 |
| Effector | CD8T_Tem_GZMK+GZMH+, CD8T_Trm_ZNF683, CD8T_Tem_GZMK+NR4A1+ |
| Exhaustion | CD8T_Tex_CXCL13, CD8T_terminal_Tex_LAYN, CD8T_prf_MKI67 |
| Suppression | CD4T_Treg_FOXP3, CD4T_Treg_CCR8, CD4T_Treg_MKI67 |
| Renewal | CD8T_Tm_IL7R, CD4T_Tn_CCR7 |

### Bassez et al. 2021 (Breast, n=29)
- Source: Lambrechts lab (lambrechtslab.sites.vib.be)
- Metadata: 1872-BIOKEY_metaData_cohort1_web.csv (whole TME), 1870-BIOKEY_metaData_tcells_cohort1_web.csv (T/NK subtypes)
- Denominator: total cells in whole TME per patient (pre-treatment)
- Inclusion: timepoint = "Pre", expansion in (E, NE), exclude n/a (n=2)
- Response: E = expander/responder (n=9), NE = non-expander/non-responder (n=20)

| Position | Bassez subtypes |
|----------|----------------|
| NK | NK_CYTO, NK_REST |
| Effector | CD8_EM, CD8_RM, CD8_EMRA |
| Exhaustion | CD8_EX, CD8_EX_Proliferating |
| Suppression | CD4_REG, CD4_REG_Proliferating |
| Renewal | CD8_N, CD4_N |

### Sade-Feldman et al. 2018 (Melanoma, n=19)
- Source: GSE120575
- Platform: Smart-Seq2 (gene-level, not cell type fractions)
- Denominator: total cells per patient (pre-treatment)
- Inclusion: pre-treatment samples only
- Response: responder (n=9), non-responder (n=10)

| Position | Sade-Feldman markers |
|----------|---------------------|
| NK | FGFBP2, NCAM1 |
| Effector | GZMB, PRF1 |
| Exhaustion | HAVCR2, TOX, ENTPD1 |
| Suppression | FOXP3, CCR8 |
| Renewal | TCF7, IL7R, CCR7 |

Note: Sade-Feldman uses gene expression per cell (Smart-Seq2), not cell type fractions.
The mapping uses mean expression of marker genes per patient as the position value.

---

## 4. Evaluation protocol

### Within-dataset (FULCRUM-S+)
- Method: Repeated stratified K-fold cross-validation
- K = 5
- Repeats = 200
- Random seed = 42
- Metric: AUC (Mann-Whitney U statistic)
- All LR models within a dataset use identical fold assignments

### Logistic regression hyperparameters
- Solver: lbfgs
- C = 1.0 (inverse regularization strength)
- max_iter = 1000
- random_state = 42
- All other parameters: scikit-learn defaults (v1.x)

### No-ML models
- FULCRUM-S ratio, T cell fraction, CYT: computed directly from fractions
- AUC computed on full dataset (no CV needed — no fitting)

---

## 5. Reported results (v14.1 verified)

### FULCRUM-S+ within-dataset
| Dataset | n | R | NR | FULCRUM-S+ | Full ML | Full ML features |
|---------|---|---|-----|-----------|---------|-----------------|
| Zhang NSCLC | 242 | 130 | 112 | 0.770 | 0.762 | 51 |
| Sade-Feldman Melanoma | 19 | 9 | 10 | 0.889 | 0.922 | 30 |
| Bassez Breast | 29 | 9 | 20 | 0.922 | 0.843 | 16 |

### No-ML baselines
| Score | Zhang | Bassez |
|-------|-------|--------|
| FULCRUM-S ratio | 0.780 | 0.089 |
| T cell fraction | 0.467 | 0.750 |
| Effector (CYT proxy) | 0.546 | 0.622 |

### Cross-dataset (train → test, C=1.0)
| Direction | AUC | Interpretation |
|-----------|-----|----------------|
| Zhang → Bassez | 0.106 | Fails — opposite regimes |
| Bassez → Zhang | 0.227 | Fails — opposite regimes |

Cross-dataset transfer fails because Zhang is quality-limited and Bassez is
abundance-limited. The structure (which features) transfers. The regime-specific
interpretation (which direction) does not. This is a structural prediction.

---

## 6. Version history of this specification

- v14.1 (2026-04-03): Initial locked specification. Bassez mapping verified
  from primary metadata. All numbers reproduced in single session.
- v14.0 (2026-04-03): FULCRUM naming. Bassez reported as 0.878 (different
  subtype mapping, not verified against primary metadata).
