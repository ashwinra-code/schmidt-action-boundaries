#!/usr/bin/env python3
"""Rebuild denominator flow and endpoint-audit table for the full-repro run."""

from __future__ import annotations

import csv

from full_repro_common import CANONICAL_ENDPOINT_AUDIT, FULL_AUDIT, FULL_RESULTS, write_csv


PARSED = FULL_RESULTS / "parsed_responses.csv"
CELLS = FULL_RESULTS / "afc_cell_table_from_raw.csv"
SURFACES = FULL_RESULTS / "surface_assembly_table.csv"
DENOM_OUT = FULL_RESULTS / "denominator_table.csv"
ENDPOINT_OUT = FULL_RESULTS / "endpoint_audit_table.csv"


def count_rows(path):
    with path.open(newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def main() -> None:
    surfaces = list(csv.DictReader(SURFACES.open(newline="")))
    parsed = list(csv.DictReader(PARSED.open(newline="")))

    complete = [r for r in surfaces if r["is_complete_32_cell_surface"] == "True"]
    incomplete = [r for r in surfaces if r["eligibility_status"] == "incomplete_32_cell_surface"]
    constant = [r for r in surfaces if r["eligibility_status"].startswith("constant_")]
    eligible = [r for r in surfaces if r["eligibility_status"] == "eligible_nonconstant_surface"]

    denominator_rows = [
        {
            "stage": "raw responses",
            "count": len(parsed),
            "inclusion_rule": "all rows emitted by parser replay from raw-response artifacts",
            "exclusion_rule": "none",
            "notes": "Includes 86,400 cross-model trial responses plus 960 GPT-Health rows.",
        },
        {
            "stage": "parsed responses",
            "count": sum(1 for r in parsed if r["parser_error_flag"] == "0"),
            "inclusion_rule": "parser emitted A/B/C/D label or structured GPT-Health fallback",
            "exclusion_rule": "parser_error_flag=1",
            "notes": "Parser failures are retained in parsed_responses.csv.",
        },
        {
            "stage": "AFC candidate cells",
            "count": count_rows(CELLS),
            "inclusion_rule": "modal prediction on gold range with lower and upper acceptable labels",
            "exclusion_rule": "fixed-gold/non-AFC rows and invalid modal labels",
            "notes": "One row per model-scenario-cell.",
        },
        {
            "stage": "AFC model-scenario groups",
            "count": len(surfaces),
            "inclusion_rule": "at least one AFC cell in model-scenario group",
            "exclusion_rule": "none",
            "notes": "Incomplete groups are preserved separately.",
        },
        {
            "stage": "complete 32-cell AFC surfaces",
            "count": len(complete),
            "inclusion_rule": "32 rows and 32 unique cell IDs",
            "exclusion_rule": "incomplete groups",
            "notes": "",
        },
        {
            "stage": "incomplete AFC surfaces",
            "count": len(incomplete),
            "inclusion_rule": "model-scenario groups with fewer than 32 unique cells",
            "exclusion_rule": "excluded from boundary-recovery estimand",
            "notes": "Preserved in surface_assembly_table.csv.",
        },
        {
            "stage": "constant complete AFC surfaces",
            "count": len(constant),
            "inclusion_rule": "complete surfaces with all labels identical",
            "exclusion_rule": "excluded from nonconstant boundary-recovery estimand",
            "notes": "Counted as flat surfaces.",
        },
        {
            "stage": "nonconstant complete AFC surfaces",
            "count": len(eligible),
            "inclusion_rule": "complete surfaces with at least one positive and one negative label",
            "exclusion_rule": "flat/constant complete surfaces",
            "notes": "",
        },
        {
            "stage": "eligible AFC recovery surfaces",
            "count": len(eligible),
            "inclusion_rule": "nonconstant complete AFC surfaces",
            "exclusion_rule": "incomplete and constant surfaces",
            "notes": "Primary recovery estimand denominator.",
        },
    ]
    write_csv(DENOM_OUT, ["stage", "count", "inclusion_rule", "exclusion_rule", "notes"], denominator_rows)

    endpoint_rows = []
    if CANONICAL_ENDPOINT_AUDIT.exists():
        for row in csv.DictReader(CANONICAL_ENDPOINT_AUDIT.open(newline="")):
            endpoint_rows.append(
                {
                    "endpoint_name": row["endpoint"],
                    "available_in_raw": row["endpoint"] in {"acceptable_floor_choice", "below_floor", "outside_range"},
                    "available_in_constructed_surface": True,
                    "ran_pipeline": row["ran_pipeline"],
                    "primary_or_exploratory": row["role"],
                    "eligible_surface_count": row["nonconstant_surfaces"],
                    "mean_hidden_BA": row["result_summary"].split("hidden BA=")[-1].split(";")[0]
                    if "hidden BA=" in row["result_summary"]
                    else "",
                    "mean_lift": row["result_summary"].split("lift=")[-1] if "lift=" in row["result_summary"] else "",
                    "notes": "Endpoint audit provenance is copied from the artifact-level audit table; AFC is rebuilt from raw-response artifacts in this run.",
                }
            )
    write_csv(
        ENDPOINT_OUT,
        [
            "endpoint_name",
            "available_in_raw",
            "available_in_constructed_surface",
            "ran_pipeline",
            "primary_or_exploratory",
            "eligible_surface_count",
            "mean_hidden_BA",
            "mean_lift",
            "notes",
        ],
        endpoint_rows,
    )

    report = [
        "# Eligibility Report",
        "",
        "The denominator flow is rebuilt from `results/full_repro/afc_cell_table_from_raw.csv` and `results/full_repro/surface_assembly_table.csv`.",
        "",
        "The endpoint-audit table includes non-AFC endpoint provenance from the existing artifact-level audit because this raw-response runner currently rebuilds AFC only.",
    ]
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    (FULL_AUDIT / "eligibility_report.md").write_text("\n".join(report))
    print("Wrote denominator and endpoint-audit tables.")


if __name__ == "__main__":
    main()
