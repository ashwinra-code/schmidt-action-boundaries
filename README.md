# Retrospective Triage Response-Surface Reproduction

This repository reproduces a retrospective proof-of-concept analysis of model triage behavior.

The analysis asks a simple question:

> If we observe part of a structured grid of model responses, can we predict how the same model behaves on the hidden parts of that grid?

The repository starts from package-local raw and structured response files, rebuilds the analysis tables, reruns the hidden-cell prediction experiment, recomputes the shuffle null, and checks that the final numbers match the reported result.

## Main result reproduced by this repository

Running the full reproduction should recover:

| Quantity | Expected value |
|---|---:|
| Mean hidden balanced accuracy | 0.746930 |
| Majority baseline | 0.525086 |
| Mean lift over majority | 0.221844 |
| Shuffle null mean | 0.522559 |
| Shuffle exceedances | 0 / 5,000 |
| Models with positive lift | 10 / 10 |

These values are recomputed by the pipeline from the included source artifacts.

## Quick start

From the repository root:

```bash
bash code/run_full_repro.sh --preflight
bash code/run_full_repro.sh --strict
```

The preflight command checks that the required input files are present and match the expected hashes.

The strict command reruns the full analysis. It regenerates outputs in:

```text
results/full_repro/
audit/full_repro/
```

It does not delete the shipped reference outputs in:

```text
results/expected/
audit/expected/
```

You can also run the final assertion directly:

```bash
python3 code/src/09_assert_final_reproduction.py --mode strict
```

Or use the Makefile:

```bash
make preflight
make reproduce
make assert
```

## What the full run does

The full reproduction pipeline:

1. validates the included source files;
2. rebuilds the trial-level response extract;
3. parses 87,360 model responses;
4. reconstructs 4,789 analysis cells;
5. verifies that the reconstructed cells match the locked reference artifact;
6. rebuilds the denominator flow:

   ```text
   150 candidate model-scenario groups
     → 4 incomplete groups
     → 146 complete 32-cell surfaces
     → 77 eligible nonconstant surfaces
   ```

7. replays 77,000 train/test split masks;
8. re-scores 1,540,000 hidden-cell predictions;
9. recomputes the 5,000-replicate label-shuffle null;
10. checks that the headline metrics match the expected values.

## What this analysis means

The reproduced result supports a narrow retrospective claim:

> In this retrospective triage dataset, hidden model behavior on a structured 32-cell response surface could be predicted above baseline from partial observation.

The primary endpoint is `acceptable_floor_choice` (AFC), a binary label derived from the model's triage recommendation. The AFC acronym appears throughout the codebase, file names, and audit reports.

The experiment observes 12 cells from each eligible 32-cell surface and predicts the remaining 20 hidden cells.

## What this analysis does not show

This repository does not show that the method works prospectively.

It also does not establish:

- detection of rare high-harm failures;
- active-search performance;
- intervention or repair success;
- clinical validity in a new prospective domain;
- scaling to larger surfaces (k=10 / q=128);
- general safety of any model.

Those are separate prospective claims and are not tested by this reproduction package.

## Repository layout

```text
.
├── README.md
├── REPRODUCING.md
├── MANIFEST.md
├── CITATION.cff
├── LICENSE
├── Makefile
├── Dockerfile
├── environment.yml
│
├── code/
│   ├── run_full_repro.sh
│   ├── run_all.sh
│   └── src/
│
├── data/
│   ├── raw/
│   │   ├── raw_input_manifest.csv
│   │   └── source_artifacts/
│   ├── canonical/
│   └── specs/
│
├── results/
│   ├── expected/
│   └── full_repro/
│
├── audit/
│   ├── expected/
│   ├── full_repro/
│   └── preflight/
│
├── docs/
└── metadata/
```

## Key folders

### `code/`

Contains the executable pipeline. The main entry point is:

```text
code/run_full_repro.sh
```

The numbered scripts in `code/src/` run the analysis in order, from input validation through final assertion.

### `data/raw/`

Contains the package-local source artifacts used by the reproduction.

The source boundary is:

| Source | Path |
|---|---|
| Cross-model response JSON tree | `data/raw/source_artifacts/cross_model/inference/` |
| Cross-model source labels | `data/raw/source_artifacts/cross_model/DataOriginal_FINAL.csv` |
| GPT-Health structured source CSV | `data/raw/source_artifacts/gpt_health/DataOriginal_FINAL.csv` |

The GPT-Health source is included as a structured CSV. A per-problem GPT-Health JSON tree is not included in this package.

### `data/canonical/`

Contains locked reference objects used for validation and comparison, such as canonical cell tables, split-mask references, and comparator outputs.

### `data/specs/`

Contains the frozen analysis specifications, including parser rules, endpoint definitions, split-mask rules, metric definitions, and null-shuffle rules.

### `results/expected/`

Contains shipped reference outputs from a successful run.

These are used for comparison. The strict reproduction regenerates corresponding outputs under `results/full_repro/`.

### `audit/expected/`

Contains shipped reference audit reports from a successful run.

The strict reproduction regenerates corresponding audit reports under `audit/full_repro/`.

### `docs/`

Contains supporting documentation for reviewers and independent analysts.

Recommended reading order:

1. `REPRODUCING.md`
2. `docs/SUMMARY_FOR_REVIEWERS.md`
3. `docs/REPRODUCTION_CLAIM.md`
4. `docs/METHODS_QA_CHECKLIST.md`
5. `docs/CLAIM_BOUNDARY.md`

## Environment

The pipeline requires Python 3.11 or later and NumPy.

### Conda

```bash
conda env create -f environment.yml
conda activate retrospective-poc
```

### Docker

```bash
docker build -t retrospective-poc .
docker run --rm retrospective-poc
```

By default, the Docker container runs:

```bash
bash code/run_full_repro.sh --strict
```

## Git LFS note

Three reference outputs in `results/expected/` are stored with Git LFS because of file size (`hidden_predictions.csv`, `parsed_responses.csv`, `null_permutation_manifest.csv`).

After cloning, run:

```bash
git lfs install
git lfs pull
```

The strict reproduction can regenerate the large outputs in `results/full_repro/`. The LFS files are primarily useful for comparing regenerated outputs against the shipped reference outputs.

## Expected final console output

A successful strict run should end with:

```text
FULL REPRO PASSED

Mean hidden balanced accuracy: 0.746930
Majority baseline: 0.525086
Mean lift: 0.221844
Shuffle null mean: 0.522559
Shuffle exceedances: 0 / 5000
Per-model lift: positive in 10 / 10
```

## Troubleshooting

### Preflight fails

Run:

```bash
bash code/run_full_repro.sh --preflight
```

Then check:

```text
audit/preflight/
```

Most preflight failures are missing files, path mismatches, or hash mismatches.

### Strict run fails

Check the newest files in:

```text
audit/full_repro/
```

The pipeline stops at the first failed validation step.

### Large reference files are missing

Run:

```bash
git lfs pull
```

The strict run can still regenerate analysis outputs, but some reference comparisons may be unavailable if LFS files were not pulled.

## Citation

See `CITATION.cff`.
