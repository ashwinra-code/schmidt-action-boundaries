#!/usr/bin/env python3
"""Assemble 32-cell AFC response surfaces from rebuilt cells."""

from __future__ import annotations

import csv
from collections import defaultdict

from full_repro_common import FULL_AUDIT, FULL_RESULTS, write_csv


CELL_IN = FULL_RESULTS / "afc_cell_table_from_raw.csv"
SURFACE_OUT = FULL_RESULTS / "surface_assembly_table.csv"

FIELDS = [
    "surface_id",
    "model_name",
    "model_snapshot",
    "scenario_id",
    "n_cells_observed",
    "is_complete_32_cell_surface",
    "n_unique_cell_ids",
    "n_duplicate_cell_ids",
    "n_missing_cell_ids",
    "missing_cell_ids",
    "is_constant_afc",
    "n_positive_afc",
    "n_negative_afc",
    "eligibility_status",
]


def main() -> None:
    if not CELL_IN.exists():
        raise SystemExit(f"Missing AFC cell table: {CELL_IN}")
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    with CELL_IN.open(newline="") as f:
        for row in csv.DictReader(f):
            groups[row["surface_id"]].append(row)

    rows: list[dict[str, object]] = []
    for surface_id, cells in groups.items():
        cell_ids = [int(r["cell_id"]) for r in cells]
        unique_ids = sorted(set(cell_ids))
        missing = [str(i) for i in range(32) if i not in unique_ids]
        positives = sum(1 for r in cells if r["acceptable_floor_choice"] == "1")
        negatives = sum(1 for r in cells if r["acceptable_floor_choice"] == "0")
        complete = len(cells) == 32 and len(unique_ids) == 32
        if not complete:
            status = "incomplete_32_cell_surface"
        elif positives == 0:
            status = "constant_zero_surface"
        elif negatives == 0:
            status = "constant_one_surface"
        else:
            status = "eligible_nonconstant_surface"
        rows.append(
            {
                "surface_id": surface_id,
                "model_name": cells[0]["model_name"],
                "model_snapshot": cells[0]["model_snapshot"],
                "scenario_id": int(cells[0]["scenario_id"]),
                "n_cells_observed": len(cells),
                "is_complete_32_cell_surface": complete,
                "n_unique_cell_ids": len(unique_ids),
                "n_duplicate_cell_ids": len(cell_ids) - len(unique_ids),
                "n_missing_cell_ids": len(missing),
                "missing_cell_ids": ";".join(missing),
                "is_constant_afc": complete and (positives == 0 or negatives == 0),
                "n_positive_afc": positives,
                "n_negative_afc": negatives,
                "eligibility_status": status,
            }
        )

    rows.sort(key=lambda r: (str(r["model_name"]), int(r["scenario_id"])))
    write_csv(SURFACE_OUT, FIELDS, rows)

    constructed = len(rows)
    incomplete = sum(1 for r in rows if r["eligibility_status"] == "incomplete_32_cell_surface")
    complete = sum(1 for r in rows if r["is_complete_32_cell_surface"] is True)
    eligible = sum(1 for r in rows if r["eligibility_status"] == "eligible_nonconstant_surface")
    constant = sum(1 for r in rows if str(r["eligibility_status"]).startswith("constant_"))

    expected = {
        "constructed_afc_groups": 150,
        "incomplete_groups": 4,
        "complete_surfaces": 146,
        "nonconstant_eligible_surfaces": 77,
    }
    observed = {
        "constructed_afc_groups": constructed,
        "incomplete_groups": incomplete,
        "complete_surfaces": complete,
        "nonconstant_eligible_surfaces": eligible,
    }

    report = [
        "# Surface Assembly Report",
        "",
        f"Constructed AFC model-scenario groups: {constructed}",
        f"Incomplete groups preserved separately: {incomplete}",
        f"Complete 32-cell AFC surfaces: {complete}",
        f"Constant complete AFC surfaces: {constant}",
        f"Eligible nonconstant complete AFC surfaces: {eligible}",
        "",
    ]
    failures = []
    for key, exp in expected.items():
        obs = observed[key]
        report.append(f"- {key}: observed {obs}, expected {exp}")
        if obs != exp:
            failures.append(f"{key}: observed {obs}, expected {exp}")
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    (FULL_AUDIT / "surface_assembly_report.md").write_text("\n".join(report))
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(1)
    print("Surface assembly denominator flow matched 150 -> 4 -> 146 -> 77.")


if __name__ == "__main__":
    main()
