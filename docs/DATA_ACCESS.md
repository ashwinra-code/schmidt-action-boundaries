# Data Access

The full-reproduction bundle is self-contained for the strict retrospective AFC proof-of-concept rerun.

An independent runner should not need any parent project tree. The default source locations are package-local:

- Raw source artifacts: `data/raw/source_artifacts/`
- Locked canonical comparators: `data/canonical/`
- Raw input manifest: `data/raw/raw_input_manifest.csv`

Advanced users may override those roots:

```bash
REPRO_RAW_ROOT=/path/to/source_artifacts \
REPRO_CANONICAL_ROOT=/path/to/canonical \
bash code/run_full_repro.sh --strict
```

Before running a destructive clean rerun, check availability:

```bash
bash code/run_full_repro.sh --preflight
```

The preflight validates file existence, row counts, and hashes before generated outputs are deleted.
