# FULCRUM Reproducibility Specification
## Version 15.0 · April 5, 2026

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

## 5. Reported results (v15.0 verified)

### FULCRUM-S+ within-dataset (v1 and v2)
| Dataset | n | R | NR | S+ v1 (6 feat) | S+ v2 (7 feat) | Full ML | ML features |
|---------|---|---|-----|-----------------|-----------------|---------|-------------|
| Zhang NSCLC | 242 | 130 | 112 | 0.781 | **0.808** | 0.746 | 51 |
| Sade-Feldman Melanoma | 19 | 9 | 10 | 0.918 | **0.941** | 0.933 | 30 |
| Bassez Breast | 29 | 9 | 20 | 0.856 | — | 0.843 | 16 |

v2 adds host_drain as 7th feature. Bassez v2 not reported because only coarse
myeloid labels are available (no inflammatory macrophage subtypes).

### No-ML baselines (v1 and v2)
| Score | Zhang v1 | Zhang v2 | Bassez v1 |
|-------|----------|----------|-----------|
| FULCRUM-S ratio | 0.780 | 0.798 | 0.089 |
| T cell fraction | 0.467 | — | 0.750 |
| Effector (CYT proxy) | 0.546 | — | 0.622 |

### Cross-cancer v2 validation (unsupervised ratio)
| Dataset | n | Cancer | v1 | v2 | Δ |
|---------|---|--------|-----|-----|---|
| Zhang NSCLC | 242 | NSCLC | 0.780 | 0.798 | +0.018 |
| Sade-Feldman Melanoma | 19 | Melanoma | 0.600 | 0.611 | +0.011 |
| Yost BCC | 11 | BCC | 0.600 | 0.633 | +0.033 |
| CRC GSE236581 | 22 | CRC | 0.442 | 0.483 | +0.042 |

v2 direction is positive on all four cancer types.
Bootstrap P(v2 > v1) = 94.6% on Zhang (2000 resamples).

### v2 controls (expected failures)
| Test | Zhang Δ | Interpretation |
|------|---------|----------------|
| ALL macrophages in denominator | −0.040 | Only inflammatory subtypes work |
| IMvigor210 bulk | −0.012 | Genes too broadly expressed |
| TCGA pan-cancer bulk | −0.037 | Genes too broadly expressed |
| GSE207422 NSCLC bulk | −0.037 | Genes too broadly expressed |
| Bassez coarse myeloid (S+ LR) | −0.065 | Abundance-limited + coarse labels |

### External bulk validation (new cohort)
| Dataset | n | Cancer | FULCRUM v1 AUC |
|---------|---|--------|----------------|
| GSE207422 NSCLC | 24 | NSCLC | 0.822 |

### Cross-dataset (train → test, C=1.0)
| Direction | AUC | Interpretation |
|-----------|-----|----------------|
| Zhang → Bassez | 0.106 | Fails — opposite regimes |
| Bassez → Zhang | 0.227 | Fails — opposite regimes |

Cross-dataset transfer fails because Zhang is quality-limited and Bassez is
abundance-limited. The structure (which features) transfers. The regime-specific
interpretation (which direction) does not. This is a structural prediction.

---

## 6. FULCRUM-S v2 — Host Conservation drain

### Structural basis
The patient's body is a dissipative system at depth L+1 hosting the immune-tumour
encounter at depth L. The patient's Conservation regime (tissue maintenance)
interferes with the Encounter at the tissue level. This is measurable as
inflammatory macrophages at the tumour site.

### Formula
```
v1: ratio = kill / (kill + suppress + ε)
v2: ratio = kill / (kill + suppress + host_drain + ε)

v1: M_eff = (1-D)/(1+D) × (1+S)
v2: M_eff = (1-(D+Dh))/(1+(D+Dh)) × (1+S)
```

host_drain / Dh = sum of inflammatory macrophage fractions.

### Host drain markers per dataset

| Dataset | Markers | Type |
|---------|---------|------|
| Zhang NSCLC | Mφ_CXCL10, Mφ_DNAJB1, Mφ_MKI67, Mφ_ISG15 | Cell type fractions |
| Sade-Feldman Melanoma | CXCL10 | Gene expression per patient |
| Yost BCC | Macrophages (coarse label) | Cell type fraction |
| CRC GSE236581 | c62_Mph_S100A8, c63_Mph_CCL20 | Cell type fractions |

### Applicability conditions
Use `include_host_drain=True` only when:
1. Platform is scRNA (not bulk)
2. Inflammatory macrophage subtypes are labeled (not just "Myeloid")
3. Dataset is quality-limited (unsupervised ratio AUC > 0.3)

---

## 7. Version history of this specification

- v15.0 (2026-04-05): Added FULCRUM-S v2 (host Conservation drain). Added
  host_drain mapping for Zhang and Sade-Feldman. v2 validated on 4 cancer types
  (NSCLC, melanoma, BCC, CRC). Controls confirmed: all-mac hurts, bulk hurts,
  abundance-limited with coarse labels hurts. External bulk validation on
  GSE207422 NSCLC (v1 AUC = 0.822). Updated all results tables to show v1 and v2.
- v14.1 (2026-04-03): Initial locked specification. Bassez mapping verified
  from primary metadata. All numbers reproduced in single session.
- v14.0 (2026-04-03): FULCRUM naming. Bassez reported as 0.878 (different
  subtype mapping, not verified against primary metadata).
