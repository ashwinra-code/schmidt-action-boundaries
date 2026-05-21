# Manifest

## Capsule Layout

```text
retrospective-poc-afc-reproduction/
  README.md
  REPRODUCING.md
  MANIFEST.md
  CITATION.cff
  LICENSE
  environment.yml
  Dockerfile
  Makefile
  code/
  data/
    raw/
    canonical/
    specs/
  results/
    expected/
    full_repro/
  audit/
    expected/
    full_repro/
    preflight/
  docs/
  metadata/
    metadata.yml
    release_checksums.tsv
```

## Artifact Roles

`data/canonical/` contains locked computational inputs and comparators. `results/expected/` and `audit/expected/` contain reference outputs for comparison only. Strict reproduction writes regenerated outputs only to `results/full_repro/` and `audit/full_repro/`.
