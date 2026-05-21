# Release Bundles

Two zip bundles are produced under `release/`.

## Code-Only / Review Bundle

`release/retrospective_poc_code_only.zip`

Contains scripts, specs, generated outputs, audit reports, and documentation. It excludes package-local raw source artifacts and locked canonical objects. Use this bundle for artifact inspection and code review, not strict standalone rerun.

## Full Reproduction Bundle

`release/retrospective_poc_full_repro_bundle.zip`

Contains the package-local raw source artifacts, canonical comparators, scripts, specs, generated outputs, audit reports, and documentation. An independent runner should be able to run:

```bash
bash code/run_full_repro.sh --preflight
bash code/run_full_repro.sh --strict
```

from the extracted folder without access to any parent project tree.
