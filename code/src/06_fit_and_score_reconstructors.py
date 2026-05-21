#!/usr/bin/env python3
"""Fit degree-1 ridge reconstructors on raw-built AFC surfaces and score hidden cells."""

from __future__ import annotations

import csv
from collections import defaultdict

from full_repro_common import (
    FULL_AUDIT,
    FULL_RESULTS,
    FULL_SPLITS,
    balanced_accuracy,
    mean,
    ridge_scores,
    write_csv,
)


CELLS = FULL_RESULTS / "afc_cell_table_from_raw.csv"
SURFACES = FULL_RESULTS / "surface_assembly_table.csv"
SPLITS = FULL_SPLITS / "q12_split_manifest.csv"
HIDDEN_OUT = FULL_RESULTS / "hidden_predictions.csv"
SPLIT_METRICS_OUT = FULL_RESULTS / "split_level_metrics.csv"
MAIN_OUT = FULL_RESULTS / "main_result_table.csv"
PER_MODEL_OUT = FULL_RESULTS / "per_model_results.csv"


def parse_ids(value: str) -> list[int]:
    return [int(v) for v in value.split(";") if v != ""]


def main() -> None:
    eligible_surface_ids = {
        row["surface_id"]
        for row in csv.DictReader(SURFACES.open(newline=""))
        if row["eligibility_status"] == "eligible_nonconstant_surface"
    }
    surfaces: dict[str, dict[str, object]] = {}
    with CELLS.open(newline="") as f:
        for row in csv.DictReader(f):
            sid = row["surface_id"]
            if sid not in eligible_surface_ids:
                continue
            if sid not in surfaces:
                surfaces[sid] = {
                    "model_name": row["model_name"],
                    "scenario_id": row["scenario_id"],
                    "diagnosis": row["diagnosis"],
                    "domain": row["domain"],
                    "labels": {},
                }
            surfaces[sid]["labels"][int(row["cell_id"])] = int(row["acceptable_floor_choice"])

    hidden_fields = [
        "surface_id",
        "split_id",
        "cell_id",
        "true_label",
        "predicted_label",
        "predicted_score",
        "is_hidden",
        "model_name",
        "scenario_id",
        "method",
    ]
    split_fields = [
        "surface_id",
        "split_id",
        "model_name",
        "scenario_id",
        "q",
        "hidden_cells",
        "observed_positive",
        "observed_negative",
        "hidden_positive",
        "hidden_negative",
        "hidden_is_one_class",
        "degree1_ba",
        "majority_ba",
        "lift_vs_majority",
    ]

    split_metric_rows: list[dict[str, object]] = []
    HIDDEN_OUT.parent.mkdir(parents=True, exist_ok=True)
    with HIDDEN_OUT.open("w", newline="") as hidden_f, SPLITS.open(newline="") as split_f:
        hidden_writer = csv.DictWriter(hidden_f, fieldnames=hidden_fields)
        hidden_writer.writeheader()
        for split in csv.DictReader(split_f):
            sid = split["surface_id"]
            if sid not in surfaces:
                continue
            labels = surfaces[sid]["labels"]
            q_ids = parse_ids(split["observed_cell_ids"])
            h_ids = parse_ids(split["hidden_cell_ids"])
            observed_y = [labels[cell_id] for cell_id in q_ids]
            hidden_y = [labels[cell_id] for cell_id in h_ids]
            scores = ridge_scores(q_ids, observed_y, h_ids, ridge_lambda=1.0)
            preds = [int(score >= 0.5) for score in scores]
            degree1_ba = balanced_accuracy(hidden_y, preds)
            majority_score = sum(observed_y) / len(observed_y)
            majority_pred = int(majority_score >= 0.5)
            majority_preds = [majority_pred] * len(h_ids)
            majority_ba = balanced_accuracy(hidden_y, majority_preds)
            split_id = split["split_id"]
            for cell_id, true_label, pred, score in zip(h_ids, hidden_y, preds, scores):
                hidden_writer.writerow(
                    {
                        "surface_id": sid,
                        "split_id": split_id,
                        "cell_id": cell_id,
                        "true_label": true_label,
                        "predicted_label": pred,
                        "predicted_score": f"{score:.15g}",
                        "is_hidden": "true",
                        "model_name": surfaces[sid]["model_name"],
                        "scenario_id": surfaces[sid]["scenario_id"],
                        "method": "degree1_ridge",
                    }
                )
            split_metric_rows.append(
                {
                    "surface_id": sid,
                    "split_id": split_id,
                    "model_name": surfaces[sid]["model_name"],
                    "scenario_id": surfaces[sid]["scenario_id"],
                    "q": 12,
                    "hidden_cells": len(h_ids),
                    "observed_positive": sum(observed_y),
                    "observed_negative": len(observed_y) - sum(observed_y),
                    "hidden_positive": sum(hidden_y),
                    "hidden_negative": len(hidden_y) - sum(hidden_y),
                    "hidden_is_one_class": int(sum(hidden_y) in {0, len(hidden_y)}),
                    "degree1_ba": f"{degree1_ba:.17g}",
                    "majority_ba": f"{majority_ba:.17g}",
                    "lift_vs_majority": f"{(degree1_ba - majority_ba):.17g}",
                }
            )

    write_csv(SPLIT_METRICS_OUT, split_fields, split_metric_rows)

    by_model: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in split_metric_rows:
        by_model[str(row["model_name"])].append(row)

    per_model_rows = []
    for model, rows in sorted(by_model.items()):
        degree1 = mean(float(r["degree1_ba"]) for r in rows)
        majority = mean(float(r["majority_ba"]) for r in rows)
        per_model_rows.append(
            {
                "model": model,
                "endpoint": "acceptable_floor_choice",
                "query_budget_cells": 12,
                "n_surfaces": len({r["surface_id"] for r in rows}),
                "n_runs": len(rows),
                "degree1_ba": f"{degree1:.17g}",
                "majority_ba": f"{majority:.17g}",
                "lift_vs_majority": f"{(degree1 - majority):.17g}",
            }
        )
    write_csv(
        PER_MODEL_OUT,
        [
            "model",
            "endpoint",
            "query_budget_cells",
            "n_surfaces",
            "n_runs",
            "degree1_ba",
            "majority_ba",
            "lift_vs_majority",
        ],
        per_model_rows,
    )

    mean_degree1 = mean(float(r["degree1_ba"]) for r in per_model_rows)
    mean_majority = mean(float(r["majority_ba"]) for r in per_model_rows)
    mean_lift = mean(float(r["lift_vs_majority"]) for r in per_model_rows)
    main_row = {
        "endpoint": "acceptable_floor_choice",
        "surface_size_cells": 32,
        "observed_q": 12,
        "hidden_cells_per_split": 20,
        "model_snapshots": len(per_model_rows),
        "mean_hidden_balanced_accuracy": f"{mean_degree1:.17g}",
        "majority_baseline": f"{mean_majority:.17g}",
        "mean_lift": f"{mean_lift:.17g}",
        "models_with_positive_lift": sum(1 for r in per_model_rows if float(r["lift_vs_majority"]) > 0),
        "total_models": len(per_model_rows),
        "aggregation": "mean of model-level means; model means are means over q12 balanced-random split masks",
    }
    write_csv(MAIN_OUT, list(main_row.keys()), [main_row])

    report = [
        "# Reconstructor Report",
        "",
        "Model family: degree-1 ridge regression",
        "Features: intercept plus five main effects",
        "Axis encoding: 0/1 cell axes transformed to -1/+1",
        "Regularization: ridge lambda=1.0; intercept penalty=1e-9",
        "Threshold: predicted score >= 0.5",
        "Solver: package-local Gauss-Jordan solver over the 6 x 6 ridge normal equations",
        "One-class observed-split handling: constant score equal to observed class",
        "One-class hidden-split handling: balanced accuracy averages only defined class recall",
        "Aggregation hierarchy: hidden cell -> split metric -> model mean -> cross-model mean",
        "",
        f"Hidden prediction rows: {len(split_metric_rows) * 20}",
        f"Split metrics: {len(split_metric_rows)}",
        f"Mean hidden BA: {main_row['mean_hidden_balanced_accuracy']}",
        f"Majority baseline: {main_row['majority_baseline']}",
        f"Mean lift: {main_row['mean_lift']}",
    ]
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    (FULL_AUDIT / "reconstructor_report.md").write_text("\n".join(report))
    print("Scored q=12 hidden-cell reconstruction from raw-built surfaces.")


if __name__ == "__main__":
    main()
