# Reviewer Summary: Retrospective AFC POC Reproduction

## Claim

The retrospective AFC proof-of-concept is reproduced from raw/structured response artifacts to the reported metrics.

The release bundle is self-contained for the strict rerun. Raw source artifacts are under `data/raw/source_artifacts/`, and locked canonical comparators are under `data/canonical/`.

## Reproduction Command

First run the non-destructive preflight:

```sh
bash code/run_full_repro.sh --preflight
```

Then run:

```sh
bash code/run_full_repro.sh --strict
```

## Passed Checks

- Raw inputs hash-validated.
- 8,640 original cross-model `results.json` files rebuilt into the trial-level raw extract.
- JSON-derived trial extract exactly matches the prior workbench extract.
- 87,360 responses parsed.
- 4,789 AFC cells rebuilt.
- Canonical AFC artifact match: 4,789 / 4,789.
- Endpoint mismatches: 0.
- Axis mismatches: 0.
- Denominator flow: 150 AFC model-scenario groups -> 4 incomplete -> 146 complete -> 77 eligible nonconstant surfaces.
- q=12 split masks replayed: 77,000.
- Hidden predictions re-scored: 1,540,000.
- Prevalence-preserving within-surface shuffle null recomputed from raw-built labels: 5,000 replicates.
- Raw-recomputed null matches frozen workbench null row-for-row.

## Reproduced Values

| Quantity | Value |
|---|---:|
| Mean hidden balanced accuracy | 0.74693002007556464 |
| Implemented majority baseline | 0.52508604978354989 |
| Mean lift | 0.22184397029201483 |
| Shuffle null mean | 0.5225585702623085 |
| Shuffle exceedances | 0 / 5,000 |
| Models with positive lift | 10 / 10 |

## Reviewer Files

- `docs/REPRODUCTION_CLAIM.md`
- `docs/CLAIM_BOUNDARY.md`
- `MANIFEST.md`
- `audit/full_repro/provenance_ledger.csv`
- `audit/full_repro/null_recompute_vs_frozen_report.md`
- `audit/full_repro/raw_rebuild_vs_canonical_artifact_report.md`
- `audit/full_repro/endpoint_attempt_ledger.md`
- `REPRODUCING.md`
- `docs/DATA_USE.md`
- `docs/CODEBOOK.md`

## Claim Boundary

This supports retrospective dense-posture AFC constructibility. It does not prove sparse high-harm recovery, active search, repair, prospective urology validity, or k=10/q=128 scaling.
