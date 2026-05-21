#!/usr/bin/env python3
"""Reproduce the retrospective POC headline from canonical workbench artifacts.

This is intentionally a narrow first-stage reproducer. It recomputes the reported
headline from the per-model q=12 table and checks it against the adjudicated
summary, then copies the small null/bootstrap summaries into this package.
"""

from __future__ import annotations

import csv
import json
from decimal import Decimal, getcontext
from pathlib import Path


getcontext().prec = 28

SRC_ROOT = Path(__file__).resolve().parent
if SRC_ROOT.parent.name == "code":
    PKG_ROOT = SRC_ROOT.parent.parent
else:
    PKG_ROOT = SRC_ROOT.parent
REPO_ROOT = PKG_ROOT

SOURCE_DIR = PKG_ROOT / "data" / "canonical"

PER_MODEL_SOURCE = SOURCE_DIR / "posture_primary_balanced_degree1_vs_baselines.csv"
SUMMARY_SOURCE = SOURCE_DIR / "posture_primary_summary.csv"
SHUFFLE_SOURCE = SOURCE_DIR / "label_shuffle_distribution_summary.csv"
BOOTSTRAP_SOURCE = SOURCE_DIR / "headline_bootstrap_ci_summary.csv"
BOOTSTRAP_REPLICATES_SOURCE = SOURCE_DIR / "headline_bootstrap_replicates.csv"
COMPARATOR_SOURCE = SOURCE_DIR / "comparator_metrics.csv"
SHUFFLE_REPLICATES_SOURCE = SOURCE_DIR / "label_shuffle_distribution_replicates.csv"
DENOMINATOR_SOURCE = SOURCE_DIR / "model_endpoint_denominators.csv"
SPLIT_MEMBERSHIP_SOURCE = SOURCE_DIR / "afc_q12_split_membership_index.csv"
RUN_MANIFEST_SOURCE = SOURCE_DIR / "primary_run_manifest.json"
FULL_CELL_SOURCE = SOURCE_DIR / "full_cell_table_constructed.csv"
BUDGET_CURVE_SOURCE = SOURCE_DIR / "budget_curve_bootstrap_ci.csv"
BUDGET_CURVE_SHAPE_SOURCE = SOURCE_DIR / "curve_shape_classification.csv"
HAMMING_DEPTH_SOURCE = SOURCE_DIR / "hamming_depth_summary.csv"

RESULTS_DIR = PKG_ROOT / "results"
AUDIT_DIR = PKG_ROOT / "audit"
SPLITS_DIR = PKG_ROOT / "data" / "splits"
PROCESSED_DIR = PKG_ROOT / "data" / "processed"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def dec(value: str) -> Decimal:
    return Decimal(value)


def mean(values: list[Decimal]) -> Decimal:
    return sum(values, Decimal("0")) / Decimal(len(values))


def assert_close(name: str, left: Decimal, right: Decimal, tolerance: Decimal) -> Decimal:
    delta = abs(left - right)
    if delta > tolerance:
        raise SystemExit(f"{name} mismatch: {left} vs {right}; delta={delta}")
    return delta


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)

    per_model_all = read_csv(PER_MODEL_SOURCE)
    primary_rows = [
        row
        for row in per_model_all
        if row["endpoint"] == "acceptable_floor_choice"
        and row["query_budget_cells"] == "12"
        and row["eligible_n_ge_5"] == "True"
    ]
    if len(primary_rows) != 10:
        raise SystemExit(f"Expected 10 eligible q=12 AFC rows; found {len(primary_rows)}")

    primary_rows.sort(key=lambda r: r["model"])
    bas = [dec(r["degree1_ba"]) for r in primary_rows]
    majority = [dec(r["majority_ba"]) for r in primary_rows]
    lifts = [dec(r["lift_vs_majority"]) for r in primary_rows]

    observed_ba = mean(bas)
    observed_majority = mean(majority)
    observed_lift = mean(lifts)
    positive_lift_n = sum(1 for v in lifts if v > 0)

    summary_rows = read_csv(SUMMARY_SOURCE)
    summary_primary = [
        row
        for row in summary_rows
        if row["endpoint"] == "acceptable_floor_choice" and row["query_budget_cells"] == "12"
    ]
    if len(summary_primary) != 1:
        raise SystemExit(f"Expected one summary row; found {len(summary_primary)}")
    summary = summary_primary[0]

    tolerance = Decimal("1e-12")
    ba_delta = assert_close(
        "mean BA",
        observed_ba,
        dec(summary["mean_degree1_ba_eligible"]),
        tolerance,
    )
    lift_delta = assert_close(
        "mean lift",
        observed_lift,
        dec(summary["mean_lift_vs_majority_eligible"]),
        tolerance,
    )

    shuffle = read_csv(SHUFFLE_SOURCE)[0]
    bootstrap = read_csv(BOOTSTRAP_SOURCE)
    bootstrap_replicates = read_csv(BOOTSTRAP_REPLICATES_SOURCE)
    comparator_rows = read_csv(COMPARATOR_SOURCE)
    shuffle_replicates = read_csv(SHUFFLE_REPLICATES_SOURCE)
    run_manifest = json.loads(RUN_MANIFEST_SOURCE.read_text())
    denominators = read_csv(DENOMINATOR_SOURCE)

    main_row = {
        "endpoint": "acceptable_floor_choice",
        "surface_size_cells": 32,
        "observed_q": 12,
        "hidden_cells_per_split": 20,
        "eligible_model_snapshots": len(primary_rows),
        "mean_hidden_balanced_accuracy": str(observed_ba),
        "majority_baseline": str(observed_majority),
        "mean_lift_over_majority": str(observed_lift),
        "positive_lift_models": positive_lift_n,
        "total_models": len(primary_rows),
        "shuffle_null_mean": shuffle["mean"],
        "shuffle_exceedances": shuffle["tail_count_ge_observed"],
        "shuffle_replicates": shuffle["permutations"],
        "shuffle_plus_one_p": shuffle["empirical_p_plus1"],
        "shuffle_z_vs_mean": shuffle["z_vs_shuffle_mean"],
        "primary_scoring": run_manifest.get("primary_scoring", ""),
        "reps_used": run_manifest.get("reps_used", ""),
        "seed": run_manifest.get("seed", ""),
    }
    write_csv(
        RESULTS_DIR / "main_result_table.csv",
        list(main_row.keys()),
        [main_row],
    )

    per_model_out: list[dict[str, object]] = []
    for row in primary_rows:
        per_model_out.append(
            {
                "model": row["model"],
                "endpoint": row["endpoint"],
                "query_budget_cells": row["query_budget_cells"],
                "n_surfaces": row["n_surfaces"],
                "degree1_ba": row["degree1_ba"],
                "majority_ba": row["majority_ba"],
                "random_score_ba": row["random_score_ba"],
                "lift_vs_majority": row["lift_vs_majority"],
                "lift_positive": str(dec(row["lift_vs_majority"]) > 0),
                "degree2_ridge_ba": row["degree2_ridge_ba"],
                "hamming_kernel_ba": row["hamming_kernel_ba"],
                "degree1_acc": row["degree1_acc"],
                "degree1_floor_recall": row["degree1_floor_recall"],
                "degree1_ceiling_recall": row["degree1_ceiling_recall"],
            }
        )
    write_csv(
        RESULTS_DIR / "per_model_results.csv",
        list(per_model_out[0].keys()),
        per_model_out,
    )

    write_csv(
        RESULTS_DIR / "null_distribution_summary.csv",
        list(shuffle.keys()),
        [shuffle],
    )
    write_csv(
        RESULTS_DIR / "bootstrap_ci_summary.csv",
        list(bootstrap[0].keys()),
        bootstrap,
    )
    write_csv(
        RESULTS_DIR / "headline_bootstrap_replicates.csv",
        list(bootstrap_replicates[0].keys()),
        bootstrap_replicates,
    )
    write_csv(
        RESULTS_DIR / "baseline_comparator_table.csv",
        list(comparator_rows[0].keys()),
        comparator_rows,
    )
    write_csv(
        RESULTS_DIR / "null_distribution.csv",
        list(shuffle_replicates[0].keys()),
        shuffle_replicates,
    )

    endpoint_rows: list[dict[str, object]] = []
    endpoints = sorted({row["endpoint"] for row in denominators})
    for endpoint in endpoints:
        rows = [row for row in denominators if row["endpoint"] == endpoint]
        total_surfaces = sum(int(row["total_surfaces"]) for row in rows)
        nonconstant_surfaces = sum(int(row["nonconstant_surfaces"]) for row in rows)
        constant_zero = sum(int(row["constant_zero_surfaces"]) for row in rows)
        constant_one = sum(int(row["constant_one_surfaces"]) for row in rows)
        models_ge5 = sum(1 for row in rows if int(row["nonconstant_surfaces"]) >= 5)
        family = rows[0]["endpoint_family"]
        if endpoint == "acceptable_floor_choice":
            role = "primary_dense_posture_poc"
            result_summary = f"q12 degree1 hidden BA={observed_ba}; lift={observed_lift}"
        elif endpoint == "floor_vs_ceiling_within_range_only":
            role = "adjacent_posture_comparator"
            fvc = [
                row
                for row in summary_rows
                if row["endpoint"] == endpoint and row["query_budget_cells"] == "12"
            ]
            result_summary = (
                f"q12 degree1 hidden BA={fvc[0]['mean_degree1_ba_eligible']}"
                if fvc
                else "posture comparator; see source results"
            )
        else:
            role = "denominator_limited_failure_endpoint"
            result_summary = "not part of dense-posture POC; denominator-limited"
        endpoint_rows.append(
            {
                "endpoint": endpoint,
                "endpoint_family": family,
                "ran_pipeline": "True",
                "role": role,
                "models_total": len(rows),
                "models_with_ge5_nonconstant_surfaces": models_ge5,
                "total_model_scenario_surfaces": total_surfaces,
                "nonconstant_surfaces": nonconstant_surfaces,
                "constant_zero_surfaces": constant_zero,
                "constant_one_surfaces": constant_one,
                "reported_in_primary_poc": str(endpoint == "acceptable_floor_choice"),
                "result_summary": result_summary,
            }
        )
    write_csv(
        RESULTS_DIR / "endpoint_audit_table.csv",
        list(endpoint_rows[0].keys()),
        endpoint_rows,
    )

    afc_denoms = [row for row in denominators if row["endpoint"] == "acceptable_floor_choice"]
    reps_used = int(run_manifest.get("reps_used", 1000))
    analyzed_splits = sum(int(row["n_surfaces"]) * reps_used for row in primary_rows)
    hidden_predictions = analyzed_splits * 20
    total_afc_surfaces = sum(int(row["total_surfaces"]) for row in afc_denoms)
    nonconstant_afc_surfaces = sum(int(row["nonconstant_surfaces"]) for row in afc_denoms)
    denom_rows = [
        {
            "step": "candidate_model_snapshots",
            "count": len(afc_denoms),
            "rule": "model snapshots present for acceptable_floor_choice denominator file",
        },
        {
            "step": "candidate_afc_model_scenario_surfaces",
            "count": total_afc_surfaces,
            "rule": "all model x scenario AFC surfaces in denominator file",
        },
        {
            "step": "constant_zero_afc_surfaces",
            "count": sum(int(row["constant_zero_surfaces"]) for row in afc_denoms),
            "rule": "all cells label 0; no recoverable boundary",
        },
        {
            "step": "constant_one_afc_surfaces",
            "count": sum(int(row["constant_one_surfaces"]) for row in afc_denoms),
            "rule": "all cells label 1; no recoverable boundary",
        },
        {
            "step": "nonconstant_afc_surfaces",
            "count": nonconstant_afc_surfaces,
            "rule": "0 < positive cells < 32; eligible boundary surfaces",
        },
        {
            "step": "models_with_ge5_nonconstant_afc_surfaces",
            "count": len(primary_rows),
            "rule": "model-level reporting threshold used for headline",
        },
        {
            "step": "primary_q12_balanced_random_split_metrics",
            "count": analyzed_splits,
            "rule": "nonconstant AFC surfaces x 1000 balanced_random q=12 split repetitions",
        },
        {
            "step": "primary_hidden_cell_scoring_events",
            "count": hidden_predictions,
            "rule": "split metrics x 20 hidden cells per split",
        },
    ]
    write_csv(RESULTS_DIR / "denominator_table.csv", ["step", "count", "rule"], denom_rows)
    write_csv(
        RESULTS_DIR / "per_model_denominator_table.csv",
        list(afc_denoms[0].keys()),
        afc_denoms,
    )

    full_cell_rows = read_csv(FULL_CELL_SOURCE)
    afc_cells = [
        row for row in full_cell_rows if row["endpoint"] == "acceptable_floor_choice"
    ]
    surface_counts: dict[str, dict[str, object]] = {}
    for row in afc_cells:
        surface_id = f"{row['endpoint']}|{row['model']}|scenario_{row['scenario_pair_id']}"
        info = surface_counts.setdefault(
            surface_id,
            {
                "surface_id": surface_id,
                "model": row["model"],
                "scenario_pair_id": row["scenario_pair_id"],
                "diagnosis": row["diagnosis"],
                "domain": row["domain"],
                "gold_triage": row["gold_triage"],
                "endpoint": row["endpoint"],
                "endpoint_family": row["endpoint_family"],
                "n_cells": 0,
                "positive_cells": 0,
            },
        )
        info["n_cells"] = int(info["n_cells"]) + 1
        info["positive_cells"] = int(info["positive_cells"]) + int(row["y"])
    surface_rows = []
    for info in sorted(surface_counts.values(), key=lambda r: (str(r["model"]), int(str(r["scenario_pair_id"])))):
        positive_cells = int(info["positive_cells"])
        info["negative_cells"] = int(info["n_cells"]) - positive_cells
        info["complete_32_cell_surface"] = str(int(info["n_cells"]) == 32)
        info["nonconstant"] = str(0 < positive_cells < int(info["n_cells"]))
        surface_rows.append(info)
    complete_surface_rows = [
        row for row in surface_rows if row["complete_32_cell_surface"] == "True"
    ]
    nonconstant_surface_rows = [
        row
        for row in complete_surface_rows
        if row["nonconstant"] == "True"
    ]
    if len(complete_surface_rows) != total_afc_surfaces:
        raise SystemExit(
            "AFC complete surface count mismatch: "
            f"{len(complete_surface_rows)} vs {total_afc_surfaces}"
        )
    if len(nonconstant_surface_rows) != nonconstant_afc_surfaces:
        raise SystemExit(
            "AFC nonconstant surface count mismatch: "
            f"{len(nonconstant_surface_rows)} vs {nonconstant_afc_surfaces}"
        )
    complete_surface_ids = {str(row["surface_id"]) for row in complete_surface_rows}
    complete_afc_cells = [
        row
        for row in afc_cells
        if f"{row['endpoint']}|{row['model']}|scenario_{row['scenario_pair_id']}"
        in complete_surface_ids
    ]
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(
        PROCESSED_DIR / "all_afc_surface_cells_including_incomplete.csv",
        list(afc_cells[0].keys()),
        afc_cells,
    )
    write_csv(
        PROCESSED_DIR / "surface_cells.csv",
        list(complete_afc_cells[0].keys()),
        complete_afc_cells,
    )
    write_csv(
        PROCESSED_DIR / "surface_manifest.csv",
        list(surface_rows[0].keys()),
        surface_rows,
    )
    write_csv(
        PROCESSED_DIR / "eligible_surfaces.csv",
        list(nonconstant_surface_rows[0].keys()),
        nonconstant_surface_rows,
    )

    budget_rows = [
        row
        for row in read_csv(BUDGET_CURVE_SOURCE)
        if row["endpoint"] == "acceptable_floor_choice"
    ]
    primary_budget_rows = [
        row for row in budget_rows if row["method"] == "degree1_ridge"
    ]
    write_csv(
        RESULTS_DIR / "q_budget_curve.csv",
        list(budget_rows[0].keys()),
        budget_rows,
    )
    write_csv(
        RESULTS_DIR / "primary_degree1_q_budget_curve.csv",
        list(primary_budget_rows[0].keys()),
        primary_budget_rows,
    )
    write_csv(
        RESULTS_DIR / "budget_curve.csv",
        list(primary_budget_rows[0].keys()),
        primary_budget_rows,
    )
    curve_shape_rows = [
        row
        for row in read_csv(BUDGET_CURVE_SHAPE_SOURCE)
        if row["endpoint"] == "acceptable_floor_choice"
    ]
    write_csv(
        RESULTS_DIR / "q_budget_curve_shape_classification.csv",
        list(curve_shape_rows[0].keys()),
        curve_shape_rows,
    )

    hamming_rows = read_csv(HAMMING_DEPTH_SOURCE)
    write_csv(
        RESULTS_DIR / "hamming_depth_table.csv",
        list(hamming_rows[0].keys()),
        hamming_rows,
    )

    SPLITS_DIR.mkdir(parents=True, exist_ok=True)
    split_rows: list[dict[str, str]] = []
    split_schema: list[str] | None = None
    one_class = 0
    with SPLIT_MEMBERSHIP_SOURCE.open(newline="") as f:
        reader = csv.DictReader(f)
        split_schema = reader.fieldnames or []
        for row in reader:
            if row["split_design"] != "balanced_random":
                continue
            split_rows.append(row)
            if row["recorded_hidden_floor_count"] == "0" or row["recorded_hidden_ceiling_count"] == "0":
                one_class += 1
    if split_schema is None:
        raise SystemExit("Split membership source had no header")
    write_csv(SPLITS_DIR / "q12_split_manifest.csv", split_schema, split_rows)
    write_csv(
        AUDIT_DIR / "split_manifest_summary.csv",
        [
            "source_path",
            "exported_path",
            "split_design",
            "query_budget_cells",
            "split_rows",
            "one_class_hidden_splits",
            "one_class_hidden_split_fraction",
            "all_checks_pass",
        ],
        [
            {
                "source_path": str(SPLIT_MEMBERSHIP_SOURCE.relative_to(REPO_ROOT)),
                "exported_path": "data/splits/q12_split_manifest.csv",
                "split_design": "balanced_random",
                "query_budget_cells": 12,
                "split_rows": len(split_rows),
                "one_class_hidden_splits": one_class,
                "one_class_hidden_split_fraction": one_class / len(split_rows),
                "all_checks_pass": str(all(row["all_checks_pass"] == "1" for row in split_rows)),
            }
        ],
    )

    provenance_rows = [
        {"artifact": "per_model_results", "source_path": str(PER_MODEL_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "summary_check", "source_path": str(SUMMARY_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "label_shuffle_summary", "source_path": str(SHUFFLE_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "bootstrap_ci_summary", "source_path": str(BOOTSTRAP_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "headline_bootstrap_replicates", "source_path": str(BOOTSTRAP_REPLICATES_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "baseline_comparator_table", "source_path": str(COMPARATOR_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "null_distribution", "source_path": str(SHUFFLE_REPLICATES_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "denominator_table", "source_path": str(DENOMINATOR_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "surface_cells", "source_path": str(FULL_CELL_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "q12_split_manifest", "source_path": str(SPLIT_MEMBERSHIP_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "q_budget_curve", "source_path": str(BUDGET_CURVE_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "q_budget_curve_shape_classification", "source_path": str(BUDGET_CURVE_SHAPE_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "hamming_depth_table", "source_path": str(HAMMING_DEPTH_SOURCE.relative_to(REPO_ROOT))},
        {"artifact": "primary_run_manifest", "source_path": str(RUN_MANIFEST_SOURCE.relative_to(REPO_ROOT))},
    ]
    write_csv(
        AUDIT_DIR / "source_artifact_manifest.csv",
        ["artifact", "source_path"],
        provenance_rows,
    )
    write_csv(
        AUDIT_DIR / "summary_consistency_check.csv",
        ["check", "recomputed_value", "summary_value", "absolute_delta", "tolerance", "pass"],
        [
            {
                "check": "mean_hidden_balanced_accuracy",
                "recomputed_value": str(observed_ba),
                "summary_value": summary["mean_degree1_ba_eligible"],
                "absolute_delta": str(ba_delta),
                "tolerance": str(tolerance),
                "pass": "True",
            },
            {
                "check": "mean_lift_over_majority",
                "recomputed_value": str(observed_lift),
                "summary_value": summary["mean_lift_vs_majority_eligible"],
                "absolute_delta": str(lift_delta),
                "tolerance": str(tolerance),
                "pass": "True",
            },
        ],
    )

    print("Main retrospective POC result")
    print("Endpoint: acceptable_floor_choice")
    print("Surface size: 32")
    print("Observed q: 12")
    print("Hidden cells per split: 20")
    print(f"Models: {len(primary_rows)}")
    print(f"Mean hidden balanced accuracy: {observed_ba:.6f}")
    print(f"Majority baseline: {observed_majority:.6f}")
    print(f"Mean lift: {observed_lift:.6f}")
    print(f"Shuffle null mean: {Decimal(shuffle['mean']):.6f}")
    print(f"Shuffle exceedances: {shuffle['tail_count_ge_observed']} / {shuffle['permutations']}")
    print(f"Per-model lift: positive in {positive_lift_n} / {len(primary_rows)}")


if __name__ == "__main__":
    main()
