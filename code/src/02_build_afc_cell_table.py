#!/usr/bin/env python3
"""Build AFC cell-level table from parsed raw responses."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict

from full_repro_common import (
    AXES,
    FULL_AUDIT,
    FULL_RESULTS,
    PKG_ROOT,
    TRIAGE_ORD,
    axes_from_source_row,
    cell_id_from_axes,
    classify_prediction,
    gold_bounds,
    modal_answer,
    write_csv,
)


PARSED = FULL_RESULTS / "parsed_responses.csv"
CELL_OUT = FULL_RESULTS / "afc_cell_table_from_raw.csv"
CROSSWALK_OUT = FULL_RESULTS / "source_to_cell_crosswalk.csv"

CELL_FIELDS = [
    "model_name",
    "model_snapshot",
    "scenario_id",
    "surface_id",
    "cell_id",
    "axis_anchor",
    "axis_access",
    "axis_black",
    "axis_woman",
    "axis_objective",
    "acceptable_floor_choice",
    "source_response_id",
    "parser_status",
    "modal_triage_label",
    "gold_triage",
    "diagnosis",
    "domain",
]

CROSSWALK_FIELDS = [
    "response_id",
    "scenario_id",
    "surface_id",
    "cell_id",
    "axis_values",
    "endpoint_values",
]


def main() -> None:
    if not PARSED.exists():
        raise SystemExit(f"Missing parsed responses: {PARSED}")

    groups: dict[tuple[str, str], dict[str, object]] = {}
    with PARSED.open(newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["model_name"], row["vignette_id"])
            if key not in groups:
                axes = axes_from_source_row(row)
                groups[key] = {
                    "model_name": row["model_name"],
                    "model_snapshot": row["model_snapshot"],
                    "scenario_id": row["scenario_id"],
                    "case_id": row["case_id"],
                    "variant_code": row["variant_code"],
                    "gold_triage": row["gold_triage"],
                    "diagnosis": row["diagnosis"],
                    "domain": row["domain"],
                    "axes": axes,
                    "labels": [],
                    "response_ids": [],
                    "parser_errors": 0,
                }
            group = groups[key]
            group["labels"].append((int(row["trial_idx"]), row["parsed_triage_label"]))
            group["response_ids"].append(row["response_id"])
            group["parser_errors"] += int(row["parser_error_flag"])

    cell_rows: list[dict[str, object]] = []
    crosswalk_rows: list[dict[str, object]] = []
    skipped_not_afc = 0
    skipped_invalid_modal = 0

    for group in groups.values():
        lo, hi = gold_bounds(str(group["gold_triage"]))
        if lo == hi:
            skipped_not_afc += 1
            continue
        labels = [label for _, label in sorted(group["labels"])]
        modal = modal_answer(labels)
        if modal not in TRIAGE_ORD:
            skipped_invalid_modal += 1
            continue
        endpoint = classify_prediction(modal, str(group["gold_triage"]))
        axes = group["axes"]
        cell_id = cell_id_from_axes(axes)
        surface_id = f"acceptable_floor_choice|{group['model_name']}|scenario_{int(str(group['scenario_id']))}"
        parser_status = "all_valid" if int(group["parser_errors"]) == 0 else "has_parser_failures"
        cell_row = {
            "model_name": group["model_name"],
            "model_snapshot": group["model_snapshot"],
            "scenario_id": int(str(group["scenario_id"])),
            "surface_id": surface_id,
            "cell_id": cell_id,
            "axis_anchor": axes["anchor"],
            "axis_access": axes["access"],
            "axis_black": axes["black"],
            "axis_woman": axes["woman"],
            "axis_objective": axes["objective"],
            "acceptable_floor_choice": endpoint["acceptable_floor_choice"],
            "source_response_id": ";".join(group["response_ids"]),
            "parser_status": parser_status,
            "modal_triage_label": modal,
            "gold_triage": group["gold_triage"],
            "diagnosis": group["diagnosis"],
            "domain": group["domain"],
        }
        cell_rows.append(cell_row)
        endpoint_values = f"acceptable_floor_choice={endpoint['acceptable_floor_choice']};modal_triage={modal}"
        axis_values = ";".join(f"{axis}={axes[axis]}" for axis in AXES)
        for response_id in group["response_ids"]:
            crosswalk_rows.append(
                {
                    "response_id": response_id,
                    "scenario_id": int(str(group["scenario_id"])),
                    "surface_id": surface_id,
                    "cell_id": cell_id,
                    "axis_values": axis_values,
                    "endpoint_values": endpoint_values,
                }
            )

    cell_rows.sort(key=lambda r: (str(r["model_name"]), int(r["scenario_id"]), int(r["cell_id"])))
    crosswalk_rows.sort(key=lambda r: (str(r["surface_id"]), int(r["cell_id"]), str(r["response_id"])))

    write_csv(CELL_OUT, CELL_FIELDS, cell_rows)
    write_csv(CROSSWALK_OUT, CROSSWALK_FIELDS, crosswalk_rows)

    by_model = Counter(str(row["model_name"]) for row in cell_rows)
    report = [
        "# Cell Construction Report",
        "",
        f"Parsed response groups considered: {len(groups)}",
        f"Skipped non-AFC fixed-gold groups: {skipped_not_afc}",
        f"Skipped invalid-modal AFC groups: {skipped_invalid_modal}",
        f"AFC cell rows emitted: {len(cell_rows)}",
        f"Source-to-cell crosswalk rows emitted: {len(crosswalk_rows)}",
        "",
        "Every emitted AFC cell traces to one or more raw `response_id`s through `results/full_repro/source_to_cell_crosswalk.csv`.",
        "",
        "AFC cells by model:",
    ]
    for model, count in sorted(by_model.items()):
        report.append(f"- {model}: {count}")
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    (FULL_AUDIT / "cell_construction_report.md").write_text("\n".join(report))
    print(f"Built {len(cell_rows)} AFC cells from parsed raw responses.")


if __name__ == "__main__":
    main()
