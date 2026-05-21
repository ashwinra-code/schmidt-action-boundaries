# Claim Language

Current status: **Tier 2B**.

Target next status: **Tier 3** after a clean-environment independent rerun.

## Tier 1 - Artifact-Level Replication

Starting from constructed AFC response-surface artifacts, the repository reproduces the grant-reported retrospective POC metrics.

## Tier 2A - Raw-Response-To-Main-Metric Reproduction With Frozen-Null Replay

Starting from raw/structured response artifacts, the repository rebuilds AFC cells, exactly matches the canonical constructed AFC artifact, reproduces the denominator flow, replays q=12 split masks, re-scores hidden predictions, and reproduces the headline BA, majority baseline, lift, and per-model positive-lift metrics. The 5,000-replicate shuffle null is replayed from a frozen workbench artifact and hash-validated, but not recomputed from raw labels inside the runner.

## Tier 2B - Strict Raw-Response-To-Result Reproduction

Starting from raw/structured response artifacts, the repository reproduces parsing, AFC cell construction, surface assembly, denominator filtering, split-mask replay, hidden-cell scoring, majority baseline, and the 5,000-replicate prevalence-preserving shuffle null from raw-rebuilt labels, recovering the reported null mean and exceedance count.

This is the current repository status after `bash code/run_full_repro.sh --strict` passes.

## Tier 3 - Independent Full Reproduction

An external runner reproduces Tier 2B in a clean environment.

## Important Input Boundary

The package rebuilds the cross-model trial-level raw extract from the package-local original per-problem JSON result tree under `data/raw/source_artifacts/cross_model/inference`. The GPT-Health source is a package-local structured raw CSV under `data/raw/source_artifacts/gpt_health/DataOriginal_FINAL.csv`. Do not claim GPT-Health JSON replay unless a per-problem GPT-Health JSON tree is supplied and made part of `run_full_repro.sh`.

The default Tier 2B runner is self-contained with package-local raw and canonical artifacts. Environment variables `REPRO_RAW_ROOT` and `REPRO_CANONICAL_ROOT` are available only for advanced alternate layouts.

## Do Not Use

- fully validated
- prospectively confirmed
- proves sparse harm recovery
- proves active search
- proves repair
- proves k=10 scaling
