#!/usr/bin/env python3
"""Generate robustness tables for the raw-response artifact replay."""

from __future__ import annotations

import csv
import math
from collections import defaultdict

from full_repro_common import (
    AXES,
    CANONICAL_BUDGET_CURVE,
    CANONICAL_HAMMING_DEPTH,
    FULL_AUDIT,
    FULL_RESULTS,
    copy_csv,
    mean,
    percentile,
    write_csv,
)


SPLIT_METRICS = FULL_RESULTS / "split_level_metrics.csv"
CELLS = FULL_RESULTS / "afc_cell_table_from_raw.csv"
SURFACES = FULL_RESULTS / "surface_assembly_table.csv"
BUDGET_OUT = FULL_RESULTS / "budget_curve.csv"
HAMMING_OUT = FULL_RESULTS / "hamming_depth_table.csv"
SPLIT_UNCERTAINTY_OUT = FULL_RESULTS / "split_uncertainty_table.csv"
SINGLE_AXIS_OUT = FULL_RESULTS / "single_axis_dominance_table.csv"
STRICT_PRIMARY = FULL_RESULTS / "strict_primary"
FROZEN_SECONDARY = FULL_RESULTS / "frozen_secondary"


def binary_ba(y: list[int], pred: list[int]) -> float:
    recalls = []
    for cls in [1, 0]:
        denom = sum(1 for v in y if v == cls)
        if denom:
            recalls.append(sum(1 for yy, pp in zip(y, pred) if yy == cls and pp == cls) / denom)
    return sum(recalls) / len(recalls)


def mutual_information(xs: list[int], ys: list[int]) -> float:
    n = len(xs)
    total = 0.0
    for x in [0, 1]:
        for y in [0, 1]:
            pxy = sum(1 for xx, yy in zip(xs, ys) if xx == x and yy == y) / n
            if pxy == 0:
                continue
            px = sum(1 for xx in xs if xx == x) / n
            py = sum(1 for yy in ys if yy == y) / n
            total += pxy * math.log2(pxy / (px * py))
    return total


def main() -> None:
    copy_csv(CANONICAL_BUDGET_CURVE, BUDGET_OUT, lambda r: r.get("endpoint") == "acceptable_floor_choice")
    copy_csv(CANONICAL_HAMMING_DEPTH, HAMMING_OUT)
    copy_csv(
        CANONICAL_BUDGET_CURVE,
        FROZEN_SECONDARY / "budget_curve.csv",
        lambda r: r.get("endpoint") == "acceptable_floor_choice",
    )
    copy_csv(CANONICAL_HAMMING_DEPTH, FROZEN_SECONDARY / "hamming_depth_table.csv")

    split_rows = list(csv.DictReader(SPLIT_METRICS.open(newline="")))
    degree1_values = [float(r["degree1_ba"]) for r in split_rows]
    degree1_mean = mean(degree1_values)
    below_majority = [
        1
        for r in split_rows
        if float(r["degree1_ba"]) < float(r["majority_ba"])
    ]
    split_uncertainty = [
        {
            "quantity": "q12_degree1_hidden_BA",
            "mean": f"{degree1_mean:.17g}",
            "sd": f"{math.sqrt(mean([(v - degree1_mean) ** 2 for v in degree1_values])):.17g}",
            "p2_5": f"{percentile(degree1_values, 0.025):.17g}",
            "p5": f"{percentile(degree1_values, 0.05):.17g}",
            "median": f"{percentile(degree1_values, 0.5):.17g}",
            "p95": f"{percentile(degree1_values, 0.95):.17g}",
            "worst_valid_split": f"{min(degree1_values):.17g}",
            "percent_splits_below_majority_baseline": f"{100 * len(below_majority) / len(split_rows):.17g}",
        }
    ]
    write_csv(
        SPLIT_UNCERTAINTY_OUT,
        [
            "quantity",
            "mean",
            "sd",
            "p2_5",
            "p5",
            "median",
            "p95",
            "worst_valid_split",
            "percent_splits_below_majority_baseline",
        ],
        split_uncertainty,
    )
    write_csv(
        STRICT_PRIMARY / "split_uncertainty_table.csv",
        [
            "quantity",
            "mean",
            "sd",
            "p2_5",
            "p5",
            "median",
            "p95",
            "worst_valid_split",
            "percent_splits_below_majority_baseline",
        ],
        split_uncertainty,
    )

    eligible_ids = {
        row["surface_id"]
        for row in csv.DictReader(SURFACES.open(newline=""))
        if row["eligibility_status"] == "eligible_nonconstant_surface"
    }
    cell_rows = [
        row
        for row in csv.DictReader(CELLS.open(newline=""))
        if row["surface_id"] in eligible_ids
    ]
    y = [int(r["acceptable_floor_choice"]) for r in cell_rows]
    y_mean = mean(y)
    total_ss = sum((v - y_mean) ** 2 for v in y)
    axis_rows = []
    for axis in AXES:
        col = f"axis_{axis}"
        x = [int(r[col]) for r in cell_rows]
        pred_same = x
        pred_flip = [1 - v for v in x]
        ba_same = binary_ba(y, pred_same)
        ba_flip = binary_ba(y, pred_flip)
        ba = max(ba_same, ba_flip)
        mean_one = mean([yy for xx, yy in zip(x, y) if xx == 1])
        mean_zero = mean([yy for xx, yy in zip(x, y) if xx == 0])
        coeff = mean_one - mean_zero
        fitted = [mean_one if xx == 1 else mean_zero for xx in x]
        explained = sum((fit - y_mean) ** 2 for fit in fitted) / total_ss if total_ss else 0.0
        axis_rows.append(
            {
                "axis": axis,
                "univariate_BA_best_orientation": f"{ba:.17g}",
                "mutual_information_bits": f"{mutual_information(x, y):.17g}",
                "main_effect_coefficient_probability_scale": f"{coeff:.17g}",
                "variance_explained": f"{explained:.17g}",
                "interpretation_note": "Pooled eligible-cell descriptive audit; not used to fit the primary reconstructor.",
            }
        )
    write_csv(
        SINGLE_AXIS_OUT,
        [
            "axis",
            "univariate_BA_best_orientation",
            "mutual_information_bits",
            "main_effect_coefficient_probability_scale",
            "variance_explained",
            "interpretation_note",
        ],
        axis_rows,
    )
    write_csv(
        STRICT_PRIMARY / "single_axis_dominance_table.csv",
        [
            "axis",
            "univariate_BA_best_orientation",
            "mutual_information_bits",
            "main_effect_coefficient_probability_scale",
            "variance_explained",
            "interpretation_note",
        ],
        axis_rows,
    )

    surface_rows = list(csv.DictReader(SURFACES.open(newline="")))
    report = [
        "# Robustness Report",
        "",
        "Generated from raw-built q=12 split metrics:",
        f"- Split uncertainty rows: {len(split_uncertainty)}",
        f"- Single-axis dominance rows: {len(axis_rows)}",
        "",
        "Replayed from frozen workbench robustness artifacts:",
        "- q budget curve",
        "- Hamming-depth recovery",
        "",
        "Namespace copies:",
        "- Strict primary generated outputs are mirrored under `results/full_repro/strict_primary/`.",
        "- Frozen secondary robustness outputs are mirrored under `results/full_repro/frozen_secondary/`.",
        "",
        "Flat-surface sensitivity denominator:",
        f"- Complete constant surfaces: {sum(1 for r in surface_rows if r['eligibility_status'].startswith('constant_'))}",
        f"- Complete nonconstant surfaces: {sum(1 for r in surface_rows if r['eligibility_status'] == 'eligible_nonconstant_surface')}",
        "",
        "The q=4 budget-curve row is reported as a retrospective stress test only, not proof of k=10/q=128 scaling.",
    ]
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    (FULL_AUDIT / "robustness_report.md").write_text("\n".join(report))
    print("Wrote robustness and sensitivity outputs.")


if __name__ == "__main__":
    main()
