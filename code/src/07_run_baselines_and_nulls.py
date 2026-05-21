#!/usr/bin/env python3
"""Recompute the prevalence-preserving shuffle null from raw-built AFC labels."""

from __future__ import annotations

import csv
import hashlib
import time
from collections import defaultdict

import numpy as np

from full_repro_common import (
    AXES,
    CANONICAL_COMPARATORS,
    CANONICAL_SHUFFLE_REPLICATES,
    FULL_AUDIT,
    FULL_RESULTS,
    mean,
    write_csv,
)


MAIN = FULL_RESULTS / "main_result_table.csv"
CELLS = FULL_RESULTS / "afc_cell_table_from_raw.csv"
SURFACES = FULL_RESULTS / "surface_assembly_table.csv"
NULL_OUT = FULL_RESULTS / "null_distribution.csv"
NULL_RAW_OUT = FULL_RESULTS / "null_distribution_raw_recomputed.csv"
NULL_PER_MODEL_OUT = FULL_RESULTS / "null_distribution_raw_recomputed_per_model.csv"
NULL_MANIFEST_OUT = FULL_RESULTS / "null_permutation_manifest.csv"
COMPARATOR_OUT = FULL_RESULTS / "baseline_comparator_table.csv"

REPLICATES = 5000
SPLIT_REPS_PER_SURFACE = 100
Q = 12
SEED = 20260512


def stable_seed(*parts, modulo=2**32 - 1) -> int:
    value = "||".join(map(str, parts))
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:16], 16) % modulo


def degree_features(x: np.ndarray, degree: int = 1) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    z = 2 * x - 1
    cols = [np.ones((x.shape[0], 1))]
    if degree >= 1:
        cols.append(z)
    return np.hstack(cols)


def ridge_hat_matrix(x: np.ndarray, train_idx: np.ndarray, hidden_idx: np.ndarray) -> np.ndarray:
    phi = degree_features(x[train_idx], degree=1)
    phi_h = degree_features(x[hidden_idx], degree=1)
    penalty = np.eye(phi.shape[1])
    penalty[0, 0] = 1e-9
    return phi_h @ np.linalg.pinv(phi.T @ phi + penalty) @ phi.T


def balanced_random_indices(x: np.ndarray, q: int, rng: np.random.Generator) -> np.ndarray:
    n = len(x)
    for _ in range(1000):
        idx = np.sort(rng.choice(n, size=q, replace=False))
        xt = x[idx]
        if all(len(np.unique(xt[:, j])) == 2 for j in range(x.shape[1])):
            return idx
    return np.sort(rng.choice(n, size=q, replace=False))


def balanced_accuracy_batch(y_true: np.ndarray, pred_bool: np.ndarray) -> np.ndarray:
    y_bool = y_true.astype(bool)
    pos = y_bool
    neg = ~y_bool
    pos_n = pos.sum(axis=1)
    neg_n = neg.sum(axis=1)
    vals = np.zeros(y_true.shape[0], dtype=float)
    cnt = np.zeros(y_true.shape[0], dtype=float)
    mask = pos_n > 0
    vals[mask] += (pred_bool[mask] & pos[mask]).sum(axis=1) / pos_n[mask]
    cnt[mask] += 1
    mask = neg_n > 0
    vals[mask] += ((~pred_bool[mask]) & neg[mask]).sum(axis=1) / neg_n[mask]
    cnt[mask] += 1
    return vals / cnt


def summarize(values: np.ndarray) -> dict[str, object]:
    return {
        "n": int(values.size),
        "mean": float(np.mean(values)),
        "sd": float(np.std(values, ddof=1)),
        "median": float(np.median(values)),
        "q025": float(np.quantile(values, 0.025)),
        "q975": float(np.quantile(values, 0.975)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def load_surfaces() -> list[dict[str, object]]:
    eligible = {
        row["surface_id"]
        for row in csv.DictReader(SURFACES.open(newline=""))
        if row["eligibility_status"] == "eligible_nonconstant_surface"
    }
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with CELLS.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["surface_id"] in eligible:
                grouped[row["surface_id"]].append(row)

    surfaces = []
    for surface_id, rows in grouped.items():
        rows = sorted(rows, key=lambda r: int(r["cell_id"]))
        y = np.array([int(r["acceptable_floor_choice"]) for r in rows], dtype=np.int8)
        if len(rows) != 32 or not (0 < int(y.sum()) < 32):
            continue
        x = np.array([[int(r[f"axis_{axis}"]) for axis in AXES] for r in rows], dtype=np.int8)
        surfaces.append(
            {
                "surface_id": surface_id,
                "model": rows[0]["model_name"],
                "scenario_id": int(rows[0]["scenario_id"]),
                "X": x,
                "y": y,
                "n_positive": int(y.sum()),
                "n_negative": int(len(y) - y.sum()),
            }
        )
    surfaces.sort(key=lambda s: (str(s["model"]), int(s["scenario_id"])))
    return surfaces


def recompute_null() -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, int], dict[str, object]]:
    surfaces = load_surfaces()
    models = sorted({str(s["model"]) for s in surfaces})
    model_scores = {model: np.zeros(REPLICATES, dtype=float) for model in models}
    model_counts = {model: 0 for model in models}
    rng = np.random.default_rng(SEED)
    t0 = time.time()

    NULL_MANIFEST_OUT.parent.mkdir(parents=True, exist_ok=True)
    with NULL_MANIFEST_OUT.open("w", newline="") as f:
        manifest = csv.DictWriter(
            f,
            fieldnames=[
                "replicate_id",
                "surface_id",
                "seed",
                "permutation_hash",
                "n_positive_preserved",
                "n_negative_preserved",
            ],
        )
        manifest.writeheader()

        for surface_index, surface in enumerate(surfaces):
            x = surface["X"]
            y = surface["y"].astype(np.int8)
            shuffled = np.empty((REPLICATES, len(y)), dtype=np.int8)
            for replicate_id in range(REPLICATES):
                shuffled[replicate_id] = rng.permutation(y)
                manifest.writerow(
                    {
                        "replicate_id": replicate_id,
                        "surface_id": surface["surface_id"],
                        "seed": SEED,
                        "permutation_hash": hashlib.sha256(shuffled[replicate_id].tobytes()).hexdigest(),
                        "n_positive_preserved": surface["n_positive"],
                        "n_negative_preserved": surface["n_negative"],
                    }
                )

            surface_score = np.zeros(REPLICATES, dtype=float)
            for split_rep in range(SPLIT_REPS_PER_SURFACE):
                split_rng = np.random.default_rng(stable_seed(SEED, "balanced_split", surface_index, split_rep))
                train_idx = balanced_random_indices(x, Q, split_rng)
                train_set = set(int(i) for i in train_idx)
                hidden_idx = np.array([i for i in range(len(y)) if i not in train_set], dtype=int)
                hat = ridge_hat_matrix(x, train_idx, hidden_idx)
                y_train = shuffled[:, train_idx]
                train_sums = y_train.sum(axis=1)
                scores = np.clip(y_train @ hat.T, 0.0, 1.0)
                scores[train_sums == 0, :] = 0.0
                scores[train_sums == len(train_idx), :] = 1.0
                pred = scores >= 0.5
                truth = shuffled[:, hidden_idx]
                surface_score += balanced_accuracy_batch(truth, pred)
            surface_score /= float(SPLIT_REPS_PER_SURFACE)
            model_scores[str(surface["model"])] += surface_score
            model_counts[str(surface["model"])] += 1

    aggregate = np.zeros(REPLICATES, dtype=float)
    per_model = {}
    for model in models:
        per_model[model] = model_scores[model] / model_counts[model]
        aggregate += per_model[model]
    aggregate /= float(len(models))
    metadata = {
        "surface_count": len(surfaces),
        "model_count": len(models),
        "runtime_seconds": time.time() - t0,
    }
    return aggregate, per_model, model_counts, metadata


def write_distribution(null_values: np.ndarray, per_model: dict[str, np.ndarray]) -> None:
    write_csv(
        NULL_RAW_OUT,
        ["replicate", "model_mean_hidden_ba"],
        (
            {"replicate": idx, "model_mean_hidden_ba": f"{value:.17g}"}
            for idx, value in enumerate(null_values)
        ),
    )
    write_csv(
        NULL_OUT,
        ["replicate", "model_mean_hidden_ba"],
        (
            {"replicate": idx, "model_mean_hidden_ba": f"{value:.17g}"}
            for idx, value in enumerate(null_values)
        ),
    )
    fields = ["replicate", *sorted(per_model)]
    rows = []
    for idx in range(REPLICATES):
        row = {"replicate": idx}
        for model in sorted(per_model):
            row[model] = f"{per_model[model][idx]:.17g}"
        rows.append(row)
    write_csv(NULL_PER_MODEL_OUT, fields, rows)


def write_comparator_table(degree1: float, majority: float, null_mean: float) -> None:
    comparator_rows = [
        {
            "comparator_or_control": "Degree-1 target-query recovery (q=12)",
            "mean_hidden_balanced_accuracy": f"{degree1:.17g}",
            "rounded": f"{degree1:.3f}",
            "source": "recomputed_from_raw_built_surfaces",
        },
        {
            "comparator_or_control": "Majority baseline",
            "mean_hidden_balanced_accuracy": f"{majority:.17g}",
            "rounded": f"{majority:.3f}",
            "source": "recomputed_from_raw_built_surfaces",
        },
        {
            "comparator_or_control": "Prevalence-preserving label-shuffle null",
            "mean_hidden_balanced_accuracy": f"{null_mean:.17g}",
            "rounded": f"{null_mean:.3f}",
            "source": "recomputed_from_raw_built_surfaces",
        },
    ]
    for row in csv.DictReader(CANONICAL_COMPARATORS.open(newline="")):
        if row["comparator_or_control"] in {
            "Degree-1 target-query recovery (q=12)",
            "Majority baseline",
            "Label-shuffled negative control",
        }:
            continue
        comparator_rows.append(
            {
                "comparator_or_control": row["comparator_or_control"],
                "mean_hidden_balanced_accuracy": row["mean_hidden_balanced_accuracy"],
                "rounded": row["rounded"],
                "source": "frozen_workbench_comparator_not_primary_null",
            }
        )
    write_csv(
        COMPARATOR_OUT,
        ["comparator_or_control", "mean_hidden_balanced_accuracy", "rounded", "source"],
        comparator_rows,
    )


def compare_to_frozen(null_values: np.ndarray) -> dict[str, object]:
    frozen = np.array(
        [
            float(row["model_mean_hidden_ba"])
            for row in csv.DictReader(CANONICAL_SHUFFLE_REPLICATES.open(newline=""))
        ],
        dtype=float,
    )
    if frozen.shape != null_values.shape:
        max_abs = float("nan")
        exact = False
    else:
        max_abs = float(np.max(np.abs(frozen - null_values)))
        exact = bool(max_abs <= 1e-12)
    return {
        "frozen_replicates": int(frozen.size),
        "raw_recomputed_replicates": int(null_values.size),
        "frozen_mean": float(np.mean(frozen)),
        "raw_recomputed_mean": float(np.mean(null_values)),
        "mean_delta": float(np.mean(null_values) - np.mean(frozen)),
        "max_abs_replicate_delta": max_abs,
        "rowwise_match_within_1e_12": exact,
    }


def main() -> None:
    main_row = next(csv.DictReader(MAIN.open(newline="")))
    degree1 = float(main_row["mean_hidden_balanced_accuracy"])
    majority = float(main_row["majority_baseline"])

    null_values, per_model, model_counts, metadata = recompute_null()
    write_distribution(null_values, per_model)
    summary = summarize(null_values)
    tail = int(np.sum(null_values >= degree1))
    summary.update(
        {
            "observed_degree1_q12_model_mean_hidden_ba": degree1,
            "tail_count_ge_observed": tail,
            "empirical_p_plus1": float((tail + 1) / (len(null_values) + 1)),
            "z_vs_shuffle_mean": float((degree1 - summary["mean"]) / summary["sd"]),
            "permutations": REPLICATES,
            "split_reps_per_surface": SPLIT_REPS_PER_SURFACE,
            "query_budget_q": Q,
            "seed": SEED,
            "runtime_seconds": metadata["runtime_seconds"],
        }
    )
    write_comparator_table(degree1, majority, float(summary["mean"]))
    comparison = compare_to_frozen(null_values)

    write_csv(
        FULL_RESULTS / "null_distribution_raw_recomputed_summary.csv",
        list(summary.keys()),
        [summary],
    )
    write_csv(
        FULL_RESULTS / "null_recompute_vs_frozen_summary.csv",
        list(comparison.keys()),
        [comparison],
    )

    report = [
        "# Null Recompute Report",
        "",
        "Null name: prevalence_preserving_within_surface_label_shuffle",
        "Shuffle unit: eligible nonconstant AFC model-scenario surface",
        "Preserves: surface ID and positive/negative label counts",
        "Destroys: coordinate-to-label assignment within each surface",
        "Split semantics: 100 q=12 balanced-random split masks per surface using the original stable-seed rule",
        "Aggregation: mean of model-level mean hidden balanced accuracy",
        "",
        f"Replicates: {summary['n']}",
        f"Eligible surfaces: {metadata['surface_count']}",
        f"Models: {metadata['model_count']}",
        f"Observed BA: {degree1:.15f}",
        f"Null mean: {summary['mean']:.15f}",
        f"Null SD: {summary['sd']:.15f}",
        f"Null exceedances >= observed: {tail} / {summary['n']}",
        f"Runtime seconds: {metadata['runtime_seconds']:.3f}",
    ]
    for model, count in sorted(model_counts.items()):
        report.append(f"- {model}: {count} surfaces")
    (FULL_AUDIT / "null_recompute_report.md").write_text("\n".join(report))

    compare_report = [
        "# Null Recompute vs Frozen Report",
        "",
        f"Frozen replicates: {comparison['frozen_replicates']}",
        f"Raw recomputed replicates: {comparison['raw_recomputed_replicates']}",
        f"Frozen mean: {comparison['frozen_mean']:.15f}",
        f"Raw recomputed mean: {comparison['raw_recomputed_mean']:.15f}",
        f"Mean delta: {comparison['mean_delta']:.15g}",
        f"Max absolute replicate delta: {comparison['max_abs_replicate_delta']:.15g}",
        f"Rowwise match within 1e-12: {comparison['rowwise_match_within_1e_12']}",
    ]
    (FULL_AUDIT / "null_recompute_vs_frozen_report.md").write_text("\n".join(compare_report))

    baseline_report = [
        "# Null and Baseline Report",
        "",
        "Degree-1 recovery and majority baseline are recomputed from raw-built AFC surfaces and replayed q=12 split masks.",
        "The 5,000-replicate prevalence-preserving shuffle null is recomputed from raw-built AFC labels using the original reviewer stress-test semantics.",
        "",
        f"Degree-1 recovery: {degree1:.12f}",
        f"Majority baseline: {majority:.12f}",
        f"Shuffle null mean: {summary['mean']:.12f}",
        f"Shuffle exceedances: {tail} / {summary['n']}",
    ]
    (FULL_AUDIT / "null_and_baseline_report.md").write_text("\n".join(baseline_report))
    print("Recomputed prevalence-preserving shuffle null from raw-built AFC labels.")


if __name__ == "__main__":
    main()
