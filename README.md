# Retrospective POC AFC Reproduction Capsule

Self-contained, deterministic reproduction of the retrospective dense-posture **AFC (acceptable-floor-choice) proof-of-concept** result. Starting from raw per-problem response JSON, the capsule rebuilds the trial-level extract, parses 87,360 responses, constructs 4,789 AFC cells, replays 77,000 q=12 split masks, re-scores 1,540,000 hidden predictions, and recomputes the 5,000-replicate prevalence-preserving shuffle null — recovering the reported headline metrics within `1e-6` and matching the frozen workbench null row-for-row to `1e-12`.

**Reproduction status:** Tier 2B (strict raw-response-to-result). Tier 3 is achieved when an external runner reproduces Tier 2B in a clean environment.

---

## Headline Metrics — what `--strict` should reproduce

| Quantity | Reproduced value |
|---|---:|
| Mean hidden balanced accuracy | `0.74693002007556464` |
| Implemented majority baseline | `0.52508604978354989` |
| Mean lift over majority | `0.22184397029201483` |
| Shuffle null mean | `0.5225585702623085` |
| Shuffle exceedances | `0 / 5,000` |
| Models with positive lift | `10 / 10` |

These full-precision values are the targets the strict runner regenerates. The assertion bar in `code/src/09_assert_final_reproduction.py` is `FLOAT_TOLERANCE = 1e-6` for floating-point metrics, exact (`COUNT_TOLERANCE = 0`) for integer counts (parsed responses, AFC cells, split masks, hidden predictions, denominator categories), and `1e-12` row-for-row for the recomputed shuffle null against the frozen workbench artifact. See `docs/REPRODUCTION_CLAIM.md` for the full passed-checks list.

---

## Quick Reference — where to find what

### Reviewer entry points

| File | Purpose |
|---|---|
| `docs/SUMMARY_FOR_REVIEWERS.md` | **Start here.** One-page summary: claim, command, passed checks, reproduced values |
| `docs/REPRODUCTION_CLAIM.md` | Full claim statement, passed-checks list, denominator flow, source-of-truth files |
| `docs/CLAIM_BOUNDARY.md` | Tier definitions (1 / 2A / 2B / 3); explicit "do not claim" language |
| `docs/LIMITATIONS_CLAIM_BOUNDARY.md` | What this reproduction does **not** show |
| `docs/METHODS_QA_CHECKLIST.md` | Reviewer QA checklist |
| `docs/INDEPENDENT_REPRODUCTION_INSTRUCTIONS.md` | Instructions for an external clean-environment rerun (Tier 3) |
| `docs/DATA_USE.md` | Permissible use of the released data |
| `docs/CODEBOOK.md` | Variable-level codebook for released CSVs |
| `MANIFEST.md` | Capsule layout and artifact-role definitions |
| `REPRODUCING.md` | Short reproduction recipe |

### Headline result artifacts (in `results/expected/`)

| File | Description |
|---|---|
| `main_result_table.csv` | Headline metrics — mean BA, baseline, lift, null mean, exceedances |
| `per_model_results.csv` | Per-model BA, majority baseline, and lift (10 models) |
| `null_distribution.csv` | Frozen 5,000-replicate shuffle null distribution |
| `null_distribution_raw_recomputed.csv` | Same null **recomputed** from raw-rebuilt labels (matches frozen to 1e-12) |
| `null_recompute_vs_frozen_summary.csv` | Row-for-row comparison summary |
| `afc_cell_table_from_raw.csv` | 4,789 AFC cells rebuilt from raw responses |
| `surface_assembly_table.csv` | 150 model-scenario rows classified `incomplete` / `complete` / `nonconstant_eligible` |
| `hidden_predictions.csv` | 1,540,000 hidden-cell predictions (Git LFS) |
| `parsed_responses.csv` | 87,360 parsed responses from raw JSON (Git LFS) |
| `null_permutation_manifest.csv` | Permutation index manifest for the shuffle null (Git LFS) |

### Audit reports (in `audit/expected/`)

| Report | What it certifies |
|---|---|
| `raw_input_validation_report.md` | Raw inputs hash-validated against `data/raw/raw_input_manifest.csv` |
| `cell_construction_report.md` | AFC cell construction from parsed raw responses |
| `raw_rebuild_vs_canonical_artifact_report.md` | 4,789 / 4,789 cell match; 0 endpoint mismatches; 0 axis mismatches |
| `endpoint_attempt_ledger.md` | Per-response endpoint-extraction attempt ledger |
| `surface_assembly_report.md` | Surface assembly diagnostics |
| `null_recompute_report.md` | Shuffle-null recomputation from raw labels |
| `null_recompute_vs_frozen_report.md` | Raw-recomputed null vs frozen workbench null |
| `metric_anomaly_replay.md` | Replay of headline metric anomalies |
| `robustness_report.md` | Sensitivity/robustness checks |
| `environment_report.md` | Runtime environment captured at run time |
| `clean_environment_probe.md` | Clean-room dependency probe |
| `provenance_ledger.csv` | Per-script provenance (inputs, outputs, hashes) |
| `strict_clean_run_terminal_transcript.txt` | Full terminal transcript of a strict pass |

### Locked specifications (in `data/specs/`)

| Spec | Defines |
|---|---|
| `raw_response_schema.yaml` | Schema for raw per-problem response JSON |
| `parser_spec.yaml` | Response parser contract |
| `endpoint_definitions.yaml` | Endpoint extraction rules |
| `axis_book.yaml` | Axis-level vocabulary |
| `eligibility_rules.yaml` | AFC-cell eligibility predicates |
| `metric_definitions.yaml` | Balanced accuracy, lift, exceedance |
| `split_mask_spec.yaml` | q=12 split-mask generation |
| `reconstructor_spec.yaml` | Hidden-cell reconstructor contract |
| `null_spec.yaml` | Prevalence-preserving shuffle-null contract |
| `model_snapshot_manifest.yaml` | Model snapshots covered by the reproduction |

---

## Setup

### Option A — conda

```bash
conda env create -f environment.yml
conda activate retrospective-poc
```

Only `python>=3.11` and `numpy` are required.

### Option B — Docker

```bash
docker build -t retrospective-poc-afc .
docker run --rm retrospective-poc-afc          # runs strict reproduction
```

The Dockerfile installs `numpy>=2.0` on top of `python:3.11-slim` and defaults to `bash code/run_full_repro.sh --strict`.

### Note — Git LFS

Three reference outputs in `results/expected/` exceed 50 MB and are stored via Git LFS (`hidden_predictions.csv` 276 MB, `parsed_responses.csv` 96 MB, `null_permutation_manifest.csv` 50 MB). After `git clone`, run:

```bash
git lfs install
git lfs pull
```

These are reference comparators only — the strict runner regenerates equivalents to `results/full_repro/`. The capsule is fully strict-runnable without pulling LFS (but the diff comparison step has nothing to compare against).

---

## Reproducing

### Standard reproduction

```bash
bash code/run_full_repro.sh --preflight    # non-destructive: validate raw inputs only
bash code/run_full_repro.sh --strict       # full strict rerun
python3 code/src/09_assert_final_reproduction.py --mode strict   # final assertion
```

Equivalent Makefile targets:

```bash
make preflight     # raw input validation
make strict        # full strict reproduction
make assert        # post-hoc assertion against EXPECTED targets
make smoke         # clean-environment probe
make clean         # remove regenerated outputs only (results/full_repro, audit/full_repro)
```

### What `--strict` does

1. Validates package-local raw inputs against `data/raw/raw_input_manifest.csv` hashes.
2. Removes and regenerates **only** `results/full_repro/`, `audit/full_repro/`, and `data/splits/full_repro/`. The shipped reference trees `results/expected/` and `audit/expected/` are preserved untouched.
3. Runs the numbered pipeline `00..12` end-to-end (parser → AFC cell rebuild → surface assembly → canonical-artifact comparison → denominator/eligibility → split-mask replay → reconstructor fit/score → metric-anomaly replay → baselines and null recompute → sensitivity/robustness → provenance write → endpoint ledger → handoff manifest).
4. Asserts pass/fail in `code/src/09_assert_final_reproduction.py` against the hardcoded `EXPECTED` targets (floats to `1e-6`, counts exact, row-wise null match to `1e-12`).

The runner is `set -euo pipefail`; failures halt immediately. Partial reports appear in `audit/full_repro/`.

### Alternate run modes

| Command | Mode |
|---|---|
| `bash code/run_full_repro.sh --strict` | Recompute the 5,000-replicate shuffle null from raw labels (Tier 2B). |
| `bash code/run_full_repro.sh --allow-frozen-null` | Replay the frozen workbench null instead of recomputing (Tier 2A). |
| `bash code/run_full_repro.sh --preflight` | Raw-input validation only, no regeneration. |

---

## Repository Structure

```
.
├── README.md                          # this file
├── REPRODUCING.md                     # short reproduction recipe
├── MANIFEST.md                        # capsule layout + artifact roles
├── CITATION.cff                       # citation metadata
├── LICENSE
├── Makefile                           # preflight / strict / assert / smoke / clean targets
├── Dockerfile                         # python:3.11-slim + numpy
├── environment.yml                    # conda env (python>=3.11, numpy)
│
├── code/
│   ├── run_full_repro.sh              # ENTRY POINT (--preflight | --strict | --allow-frozen-null)
│   ├── run_all.sh                     # legacy artifact-builder
│   └── src/                           # numbered pipeline scripts 00..12
│       ├── 00_validate_raw_inputs.py
│       ├── 00b_build_trial_extract_from_json.py
│       ├── 01_parse_raw_responses.py
│       ├── 02_build_afc_cell_table.py
│       ├── 03_assemble_surfaces.py
│       ├── 03b_compare_rebuilt_to_canonical_artifacts.py
│       ├── 04_denominator_and_eligibility.py
│       ├── 05_generate_or_replay_split_masks.py
│       ├── 06_fit_and_score_reconstructors.py
│       ├── 06b_metric_anomaly_replay.py
│       ├── 07_run_baselines_and_nulls.py
│       ├── 08_sensitivity_and_robustness.py
│       ├── 08b_write_environment_and_provenance.py
│       ├── 09_assert_final_reproduction.py
│       ├── 10_clean_environment_probe.py
│       ├── 11_build_endpoint_attempt_ledger.py
│       └── 12_build_handoff_manifest.py
│
├── data/
│   ├── raw/                           # package-local raw source artifacts (hash-manifest)
│   │   ├── raw_input_manifest.csv
│   │   └── source_artifacts/          # cross_model JSON + gpt_health CSV
│   ├── canonical/                     # locked computational inputs & comparators
│   └── specs/                         # YAML specs (parser, endpoints, axes, splits, ...)
│
├── results/
│   ├── expected/                      # shipped reference outputs (read-only, for comparison)
│   └── full_repro/                    # regenerated by --strict (deleted+rewritten each run)
│
├── audit/
│   ├── expected/                      # shipped reference audit reports
│   ├── full_repro/                    # regenerated audit reports
│   └── preflight/                     # preflight validation outputs
│
├── docs/                              # reviewer-facing method notes (see Quick Reference)
└── metadata/
    ├── metadata.yml                   # capsule metadata
    └── release_checksums.tsv          # payload checksums
```

---

## Denominator Flow

```
150 AFC model-scenario groups
  ├── 4   incomplete groups (preserved separately)
  └── 146 complete 32-cell surfaces
        └── 77 nonconstant eligible surfaces  → used for boundary recovery
```

Downstream of the 77 eligible surfaces, the strict run replays 77,000 q=12 split masks, re-scores 1,540,000 hidden-cell predictions, and recomputes a 5,000-replicate prevalence-preserving shuffle null indexed across the 77 surfaces (385,000-row permutation manifest, 5,000 × 77).

---

## Scope and Claim Boundary

**This capsule supports:** retrospective dense-posture AFC constructibility from raw responses — i.e., that the reported headline metrics are deterministically recoverable (within the tolerances above) from the per-problem JSON tree under `data/raw/source_artifacts/cross_model/inference`.

**This capsule does not support:**
- Sparse high-harm recovery
- Prospective urology validity
- Active-search success
- Repair success
- k=10 / q=128 scaling
- Universal low-degree structure
- Population-level inference over all frontier models

See `docs/CLAIM_BOUNDARY.md` for the formal tier definitions and forbidden-phrase list, and `docs/LIMITATIONS_CLAIM_BOUNDARY.md` for the scope-boundary statement and wording constraint.

---

## Input Boundary

| Source | Path |
|---|---|
| Cross-model raw JSON tree | `data/raw/source_artifacts/cross_model/inference/` |
| Cross-model gold labels | `data/raw/source_artifacts/cross_model/DataOriginal_FINAL.csv` |
| GPT-Health raw responses | `data/raw/source_artifacts/gpt_health/DataOriginal_FINAL.csv` |
| Locked canonical comparators | `data/canonical/` |

GPT-Health is sourced from a structured raw CSV (no per-problem GPT-Health JSON tree is present in this package). Environment variables `REPRO_RAW_ROOT` and `REPRO_CANONICAL_ROOT` are available for advanced alternate layouts.

---

## Citation

See `CITATION.cff`.
