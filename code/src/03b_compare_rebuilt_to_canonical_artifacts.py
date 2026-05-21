#!/usr/bin/env python3
"""Compare rebuilt AFC cells against the canonical constructed artifact."""

from __future__ import annotations

import csv

from full_repro_common import CANONICAL_FULL_CELL_SOURCE, FULL_AUDIT, FULL_RESULTS, write_csv


REBUILT = FULL_RESULTS / "afc_cell_table_from_raw.csv"
MISMATCH_OUT = FULL_RESULTS / "raw_vs_canonical_mismatches.csv"

FIELDS = [
    "surface_id",
    "cell_id",
    "field",
    "canonical_value",
    "rebuilt_value",
    "source_response_id",
    "resolution_status",
]


def canonical_key(row: dict[str, str]) -> tuple[str, int]:
    surface_id = f"{row['endpoint']}|{row['model']}|scenario_{int(row['scenario_pair_id'])}"
    return (surface_id, int(row["cell_id"]))


def rebuilt_key(row: dict[str, str]) -> tuple[str, int]:
    return (row["surface_id"], int(row["cell_id"]))


def main() -> None:
    canonical = {}
    with CANONICAL_FULL_CELL_SOURCE.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["endpoint"] == "acceptable_floor_choice":
                canonical[canonical_key(row)] = row

    rebuilt = {}
    with REBUILT.open(newline="") as f:
        for row in csv.DictReader(f):
            rebuilt[rebuilt_key(row)] = row

    mismatches: list[dict[str, object]] = []
    matching_cells = 0
    for key in sorted(set(canonical) | set(rebuilt)):
        can = canonical.get(key)
        reb = rebuilt.get(key)
        if can is None:
            mismatches.append(
                {
                    "surface_id": key[0],
                    "cell_id": key[1],
                    "field": "row_presence",
                    "canonical_value": "missing",
                    "rebuilt_value": "present",
                    "source_response_id": reb.get("source_response_id", "") if reb else "",
                    "resolution_status": "unresolved_extra_rebuilt_cell",
                }
            )
            continue
        if reb is None:
            mismatches.append(
                {
                    "surface_id": key[0],
                    "cell_id": key[1],
                    "field": "row_presence",
                    "canonical_value": "present",
                    "rebuilt_value": "missing",
                    "source_response_id": "",
                    "resolution_status": "unresolved_missing_rebuilt_cell",
                }
            )
            continue
        field_map = {
            "endpoint_label": (can["y"], reb["acceptable_floor_choice"]),
            "axis_anchor": (can["anchor"], reb["axis_anchor"]),
            "axis_access": (can["access"], reb["axis_access"]),
            "axis_black": (can["black"], reb["axis_black"]),
            "axis_woman": (can["woman"], reb["axis_woman"]),
            "axis_objective": (can["objective"], reb["axis_objective"]),
        }
        cell_ok = True
        for field, (can_val, reb_val) in field_map.items():
            if str(can_val) != str(reb_val):
                cell_ok = False
                mismatches.append(
                    {
                        "surface_id": key[0],
                        "cell_id": key[1],
                        "field": field,
                        "canonical_value": can_val,
                        "rebuilt_value": reb_val,
                        "source_response_id": reb.get("source_response_id", ""),
                        "resolution_status": "unresolved_value_mismatch",
                    }
                )
        if cell_ok:
            matching_cells += 1

    write_csv(MISMATCH_OUT, FIELDS, mismatches)
    endpoint_mismatch_count = sum(1 for r in mismatches if r["field"] == "endpoint_label")
    axis_mismatch_count = sum(1 for r in mismatches if str(r["field"]).startswith("axis_"))
    missing = sum(1 for r in mismatches if r["resolution_status"] == "unresolved_missing_rebuilt_cell")
    extra = sum(1 for r in mismatches if r["resolution_status"] == "unresolved_extra_rebuilt_cell")

    report = [
        "# Raw Rebuild vs Canonical Artifact Report",
        "",
        f"Number of matching cells: {matching_cells}",
        f"Number of mismatched cells: {len({(r['surface_id'], r['cell_id']) for r in mismatches})}",
        f"Number of missing cells: {missing}",
        f"Number of extra cells: {extra}",
        f"Endpoint label mismatch count: {endpoint_mismatch_count}",
        f"Axis mismatch count: {axis_mismatch_count}",
        "Surface assignment mismatch count: counted as missing/extra row presence mismatches",
    ]
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    (FULL_AUDIT / "raw_rebuild_vs_canonical_artifact_report.md").write_text("\n".join(report))

    if mismatches:
        print(f"FAIL: rebuilt AFC cells differ from canonical artifact; see {MISMATCH_OUT}")
        raise SystemExit(1)
    print(f"Rebuilt AFC cells exactly matched {matching_cells} canonical cells.")


if __name__ == "__main__":
    main()
