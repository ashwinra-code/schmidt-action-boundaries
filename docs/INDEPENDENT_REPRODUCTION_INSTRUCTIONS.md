# Independent Reproduction Instructions

These instructions are for an analyst who receives only this repository folder.

## 1. Unpack

Unzip or clone the full reproduction bundle. The folder should contain:

- `data/raw/source_artifacts/`
- `data/canonical/`
- `src/`
- `data/specs/`
- `run_full_repro.sh`

No parent project directory is required.

## 2. Preflight

Run:

```bash
bash code/run_full_repro.sh --preflight
```

Expected result:

```text
Raw input validation passed for 3 files.
PREFLIGHT PASSED
```

Preflight validates source-file existence, row counts, and hashes before any generated outputs are cleaned.

## 3. Strict Reproduction

Run:

```bash
bash code/run_full_repro.sh --strict
```

Expected final result:

```text
FULL REPRO CLAIM PASSED
Mean hidden balanced accuracy: 0.74693002007556464
Majority baseline: 0.52508604978354989
Mean lift: 0.22184397029201483
Shuffle null mean: 0.5225585702623085
Shuffle exceedances: 0 / 5000
Per-model lift: positive in 10 / 10
FULL REPRO PASSED
```

Expected local disk use is under 1 GB after generated outputs. Runtime depends on machine speed; the shuffle-null recomputation is the slowest step.

Observed in one Linux container test after the robustness performance patch:

- Runtime: approximately 3-4 minutes.
- Max memory: approximately 925 MB.

## 4. Docker

If Docker is available:

```bash
docker build -t retrospective-poc-full-repro .
docker run --rm retrospective-poc-full-repro
```

## 5. Files To Return For Signoff

An independent runner should return:

- `audit/full_repro/environment_report.md`
- `audit/full_repro/provenance_ledger.csv`
- `audit/full_repro/raw_input_validation_report.md`
- `audit/full_repro/null_recompute_report.md`
- `audit/full_repro/strict_clean_run_terminal_transcript.txt`
- `results/full_repro/main_result_table.csv`
- `results/full_repro/null_distribution_raw_recomputed.csv`

## Tier 3 Signoff Template

```text
Tier 3 independent reproduction signoff
Runner:
Machine:
OS:
Python:
Command:
Result:
Final metrics:
Package hash:
Notes:
```
