# Retrospective POC AFC Reproduction Capsule

This capsule is a self-contained raw/structured-response reproduction of the retrospective dense-posture AFC proof-of-concept analysis.

Run the strict reproduction from the extracted capsule root:

```bash
bash code/run_full_repro.sh --strict
```

The run writes regenerated outputs to `results/full_repro/` and `audit/full_repro/`. Shipped reference outputs are isolated in `results/expected/` and `audit/expected/` for comparison only.

Expected final metrics:

- Mean hidden balanced accuracy: `0.746930`
- Majority baseline: `0.525086`
- Mean lift over majority: `0.221844`
- Shuffle null mean: `0.522559`
- Shuffle exceedances: `0 / 5000`
- Per-model lift: positive in `10 / 10`

Directory map:

- `code/`: reproduction runners and Python source
- `data/raw/`: package-local raw source artifacts
- `data/canonical/`: locked computational inputs and comparators
- `data/specs/`: method and schema specifications
- `results/expected/` and `audit/expected/`: shipped reference outputs
- `results/full_repro/` and `audit/full_repro/`: regenerated outputs
- `docs/`: reviewer-facing method notes and scope documents
- `metadata/`: capsule metadata and payload checksums

Scope boundary: this is a retrospective dense-posture positive-control reproduction. It does not establish sparse high-harm recovery, active search, intervention repair, prospective clinical validity, or larger-budget scaling.
