#!/usr/bin/env python3
"""Assert final reproduction values and claim-tier status."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from full_repro_common import FULL_AUDIT, FULL_RESULTS, FULL_SPLITS


EXPECTED = {
    "mean_hidden_balanced_accuracy": 0.746930,
    "majority_baseline": 0.525086,
    "mean_lift": 0.221844,
    "shuffle_null_mean": 0.522559,
    "shuffle_exceedances": 0,
    "shuffle_replicates": 5000,
    "models_with_positive_lift": 10,
    "total_models": 10,
    "constructed_afc_groups": 150,
    "incomplete_groups": 4,
    "complete_surfaces": 146,
    "nonconstant_eligible_surfaces": 77,
    "parsed_responses": 87360,
    "afc_cells": 4789,
    "q12_split_masks": 77000,
    "hidden_predictions": 1540000,
}

COUNT_TOLERANCE = 0
FLOAT_TOLERANCE = 1e-6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["strict", "allow-frozen-null"],
        default="strict",
        help="strict requires raw null recomputation; allow-frozen-null permits Tier 2A status.",
    )
    return parser.parse_args()


def first_row(path: Path) -> dict[str, str]:
    return next(csv.DictReader(path.open(newline="")))


def row_count(path: Path) -> int:
    with path.open(newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def check_float(name: str, observed: float, failures: list[str]) -> bool:
    expected = EXPECTED[name]
    ok = abs(observed - expected) <= FLOAT_TOLERANCE
    if not ok:
        failures.append(f"{name}: observed {observed}, expected {expected}")
    return ok


def check_count(name: str, observed: int, failures: list[str]) -> bool:
    expected = int(EXPECTED[name])
    ok = abs(observed - expected) <= COUNT_TOLERANCE
    if not ok:
        failures.append(f"{name}: observed {observed}, expected {expected}")
    return ok


def report_matrix(assertions: dict[str, bool]) -> None:
    print("Assertion matrix:")
    for name, passed in assertions.items():
        print(f"- {name}: {'PASS' if passed else 'FAIL'}")


def main() -> None:
    args = parse_args()
    failures: list[str] = []
    assertions: dict[str, bool] = {}

    assertions["raw_inputs"] = (FULL_AUDIT / "raw_input_validation_report.md").exists()
    assertions["parser_replay"] = check_count(
        "parsed_responses",
        row_count(FULL_RESULTS / "parsed_responses.csv"),
        failures,
    )
    assertions["cell_rebuild"] = check_count(
        "afc_cells",
        row_count(FULL_RESULTS / "afc_cell_table_from_raw.csv"),
        failures,
    )

    canonical_report = (FULL_AUDIT / "raw_rebuild_vs_canonical_artifact_report.md").read_text()
    assertions["canonical_match"] = (
        "Number of matching cells: 4789" in canonical_report
        and "Endpoint label mismatch count: 0" in canonical_report
        and "Axis mismatch count: 0" in canonical_report
    )
    if not assertions["canonical_match"]:
        failures.append("canonical_match: rebuilt AFC cells do not exactly match canonical artifact")

    main = first_row(FULL_RESULTS / "main_result_table.csv")
    surface_rows = list(csv.DictReader((FULL_RESULTS / "surface_assembly_table.csv").open(newline="")))
    denominator_ok = all(
        [
            check_count("constructed_afc_groups", len(surface_rows), failures),
            check_count(
                "incomplete_groups",
                sum(1 for r in surface_rows if r["eligibility_status"] == "incomplete_32_cell_surface"),
                failures,
            ),
            check_count(
                "complete_surfaces",
                sum(1 for r in surface_rows if r["is_complete_32_cell_surface"] == "True"),
                failures,
            ),
            check_count(
                "nonconstant_eligible_surfaces",
                sum(1 for r in surface_rows if r["eligibility_status"] == "eligible_nonconstant_surface"),
                failures,
            ),
        ]
    )
    assertions["denominator_flow"] = denominator_ok
    assertions["split_mask_replay"] = check_count(
        "q12_split_masks",
        row_count(FULL_SPLITS / "q12_split_manifest.csv"),
        failures,
    )
    assertions["hidden_prediction_scoring"] = check_count(
        "hidden_predictions",
        row_count(FULL_RESULTS / "hidden_predictions.csv"),
        failures,
    )

    headline_ok = all(
        [
            check_float("mean_hidden_balanced_accuracy", float(main["mean_hidden_balanced_accuracy"]), failures),
            check_float("majority_baseline", float(main["majority_baseline"]), failures),
            check_float("mean_lift", float(main["mean_lift"]), failures),
            check_count("models_with_positive_lift", int(main["models_with_positive_lift"]), failures),
            check_count("total_models", int(main["total_models"]), failures),
        ]
    )
    assertions["headline_metrics"] = headline_ok

    null_values = [
        float(row["model_mean_hidden_ba"])
        for row in csv.DictReader((FULL_RESULTS / "null_distribution.csv").open(newline=""))
    ]
    shuffle_mean = sum(null_values) / len(null_values)
    exceedances = sum(1 for value in null_values if value >= float(main["mean_hidden_balanced_accuracy"]))
    frozen_null_ok = all(
        [
            check_count("shuffle_replicates", len(null_values), failures),
            check_float("shuffle_null_mean", shuffle_mean, failures),
            check_count("shuffle_exceedances", exceedances, failures),
        ]
    )
    assertions["frozen_null_replay"] = frozen_null_ok

    raw_null_summary = FULL_RESULTS / "null_recompute_vs_frozen_summary.csv"
    raw_null_report = FULL_AUDIT / "null_recompute_report.md"
    if raw_null_summary.exists() and raw_null_report.exists():
        raw_compare = first_row(raw_null_summary)
        raw_null_ok = (
            raw_compare["raw_recomputed_replicates"] == "5000"
            and abs(float(raw_compare["raw_recomputed_mean"]) - EXPECTED["shuffle_null_mean"]) <= FLOAT_TOLERANCE
            and float(raw_compare["max_abs_replicate_delta"]) <= 1e-12
            and raw_compare["rowwise_match_within_1e_12"] == "True"
            and row_count(FULL_RESULTS / "null_permutation_manifest.csv") == 385000
        )
    else:
        raw_null_ok = False
    assertions["raw_null_recompute"] = raw_null_ok
    if args.mode == "strict" and not raw_null_ok:
        failures.append("raw_null_recompute: 5,000-replicate shuffle null was not regenerated from raw-built labels")

    strict_required = [
        "raw_inputs",
        "parser_replay",
        "cell_rebuild",
        "canonical_match",
        "denominator_flow",
        "split_mask_replay",
        "hidden_prediction_scoring",
        "headline_metrics",
        "raw_null_recompute",
    ]
    tier2a_required = [
        "raw_inputs",
        "parser_replay",
        "cell_rebuild",
        "canonical_match",
        "denominator_flow",
        "split_mask_replay",
        "hidden_prediction_scoring",
        "headline_metrics",
        "frozen_null_replay",
    ]
    strict_pass = all(assertions[name] for name in strict_required)
    tier2a_pass = all(assertions[name] for name in tier2a_required)

    if args.mode == "allow-frozen-null":
        required_pass = tier2a_pass
    else:
        required_pass = strict_pass

    if not required_pass or failures:
        if strict_pass:
            print("STRICT RAW-RESPONSE-TO-RESULT REPRODUCTION PASSED")
        else:
            print("Strict full repro: FAIL")
        print(f"Tier 2A status: {'PASS' if tier2a_pass else 'FAIL'}")
        print(f"Tier 2B status: {'PASS' if strict_pass else 'FAIL'}")
        print()
        report_matrix(assertions)
        print()
        for failure in failures:
            print(f"FAIL: {failure}")
        if args.mode == "allow-frozen-null" and tier2a_pass:
            print()
            print("RAW-TO-MAIN-METRIC REPRODUCTION PASSED")
            print("FROZEN-NULL REPLAY PASSED")
            print("STRICT FULL RAW-TO-RESULT REPRODUCTION NOT CLAIMED")
            raise SystemExit(0)
        raise SystemExit(1)

    if args.mode == "allow-frozen-null" and not strict_pass:
        print("RAW-TO-MAIN-METRIC REPRODUCTION PASSED")
        print("FROZEN-NULL REPLAY PASSED")
        print("STRICT FULL RAW-TO-RESULT REPRODUCTION NOT CLAIMED")
        print("Reason: 5,000-replicate shuffle null replayed from frozen workbench artifact, not recomputed from raw labels.")
        raise SystemExit(0)

    print("STRICT RAW-RESPONSE-TO-RESULT REPRODUCTION PASSED")
    print("Tier 2A status: PASS")
    print("Tier 2B status: PASS")
    print()
    print("Raw/structured responses -> parser replay -> AFC cells -> exact canonical surface match -> denominator flow -> split masks -> hidden-cell reconstruction -> raw-label shuffle null -> final metrics")
    print()
    print(f"Mean hidden balanced accuracy: {float(main['mean_hidden_balanced_accuracy']):.6f}")
    print(f"Majority baseline: {float(main['majority_baseline']):.6f}")
    print(f"Mean lift: {float(main['mean_lift']):.6f}")
    print(f"Shuffle null mean: {shuffle_mean:.6f}")
    print(f"Shuffle exceedances: {exceedances} / {len(null_values)}")
    print(f"Per-model lift: positive in {main['models_with_positive_lift']} / {main['total_models']}")
    print()
    print("Denominator:")
    print("150 AFC model-scenario groups")
    print("4 incomplete groups preserved separately")
    print("146 complete 32-cell surfaces")
    print("77 nonconstant eligible surfaces")


if __name__ == "__main__":
    main()
