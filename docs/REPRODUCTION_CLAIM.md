# Full Reproduction Claim Status

Current status: **Tier 2B - strict raw-response-to-result reproduction**.

This repository reproduces the retrospective dense-posture AFC proof-of-concept result from raw/structured response artifacts through parsing, AFC cell construction, response-surface assembly, denominator filtering, split-mask replay, hidden-cell reconstruction, prevalence-preserving shuffle-null recomputation, and final reported metrics.

## Passed Strict Raw-Rebuild Checks

- Raw/structured inputs hash-validated.
- 8,640 original cross-model `results.json` files rebuilt into the trial-level raw extract.
- JSON-derived trial extract exactly matches the prior workbench extract.
- 87,360 responses parsed.
- 4,789 AFC cells rebuilt.
- Canonical AFC artifact match: 4,789 / 4,789.
- Endpoint mismatches: 0.
- Axis mismatches: 0.
- Denominator flow reproduced: 150 -> 4 incomplete -> 146 complete -> 77 eligible.
- q=12 split masks replayed: 77,000.
- Hidden predictions re-scored: 1,540,000.
- Prevalence-preserving shuffle null recomputed from raw-built labels: 5,000 replicates.
- Raw recomputed null matches frozen workbench null row-for-row within `1e-12`.

## Reproduced Values

| Quantity | Value |
|---|---:|
| Mean hidden balanced accuracy | 0.74693002007556464 |
| Implemented majority baseline | 0.52508604978354989 |
| Mean lift | 0.22184397029201483 |
| Shuffle null mean | 0.5225585702623085 |
| Shuffle exceedances | 0 / 5000 |
| Models with positive lift | 10 / 10 |

## Denominator Flow

150 AFC model-scenario groups  
4 incomplete groups preserved separately  
146 complete 32-cell surfaces  
77 nonconstant eligible surfaces used for boundary-recovery analysis

## Reproduction Command

```bash
bash code/run_full_repro.sh --strict
```

## Source-of-Truth Files

Raw inputs:

- `data/raw/raw_input_manifest.csv`
- `data/raw/source_artifacts/cross_model/inference/`
- `data/raw/source_artifacts/cross_model/DataOriginal_FINAL.csv`
- `data/raw/source_artifacts/gpt_health/DataOriginal_FINAL.csv`

Specs:

- `data/specs/raw_response_schema.yaml`
- `data/specs/parser_spec.yaml`
- `data/specs/endpoint_definitions.yaml`
- `data/specs/axis_book.yaml`
- `data/specs/eligibility_rules.yaml`
- `data/specs/metric_definitions.yaml`
- `data/specs/split_mask_spec.yaml`
- `data/specs/reconstructor_spec.yaml`
- `data/specs/null_spec.yaml`

Generated outputs:

- `results/full_repro/main_result_table.csv`
- `results/full_repro/per_model_results.csv`
- `results/full_repro/null_distribution_raw_recomputed.csv`
- `results/full_repro/null_permutation_manifest.csv`
- `results/full_repro/budget_curve.csv`
- `results/full_repro/hamming_depth_table.csv`
- `results/full_repro/single_axis_dominance_table.csv`

## Input Boundary

The cross-model source is the package-local original per-problem JSON result tree under `data/raw/source_artifacts/cross_model/inference`. GPT-Health is sourced from the package-local structured raw CSV under `data/raw/source_artifacts/gpt_health/DataOriginal_FINAL.csv` because no per-problem GPT-Health JSON tree is present in this package.

Locked canonical comparators and secondary frozen objects are package-local under `data/canonical`.

## Claim Boundary

This is a retrospective dense-posture positive-control reproduction. It does not prove sparse high-harm recovery, active search, repair, prospective urology validity, or k=10/q=128 scaling.
