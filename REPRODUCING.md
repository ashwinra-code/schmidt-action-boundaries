# Reproducing

From a fresh extraction:

```bash
unzip retrospective_poc_full_repro_capsule.zip
cd retrospective-poc-afc-reproduction
bash code/run_full_repro.sh --strict
```

Optional preflight validation:

```bash
bash code/run_full_repro.sh --preflight
```

Final assertion command:

```bash
python3 code/src/09_assert_final_reproduction.py --mode strict
```

Strict runs first validate package-local raw inputs, then remove and regenerate only `results/full_repro/`, `audit/full_repro/`, and `data/splits/full_repro/`. The shipped reference trees `results/expected/` and `audit/expected/` are preserved.

Expected final metrics:

- Mean hidden balanced accuracy: `0.746930`
- Majority baseline: `0.525086`
- Mean lift over majority: `0.221844`
- Shuffle null mean: `0.522559`
- Shuffle exceedances: `0 / 5000`
- Per-model lift: positive in `10 / 10`

The code-only archive omits raw data, canonical comparators, regenerated results, and regenerated audit outputs. It is intended for inspection only and is not strict-runnable without the omitted data.
