#!/usr/bin/env python3
"""Build reviewer-facing endpoint-attempt provenance ledger from machine artifacts."""

from __future__ import annotations

import csv

from full_repro_common import FULL_AUDIT, FULL_RESULTS, PKG_ROOT, write_csv


SOURCE = FULL_RESULTS / "endpoint_audit_table.csv"
OUT_CSV = FULL_AUDIT / "endpoint_attempt_ledger.csv"
OUT_MD = FULL_AUDIT / "endpoint_attempt_ledger.md"


def main() -> None:
    rows = list(csv.DictReader(SOURCE.open(newline="")))
    ledger = []
    for row in rows:
        endpoint = row["endpoint_name"]
        if endpoint == "acceptable_floor_choice":
            provenance = "primary dense-posture POC endpoint; raw-rebuilt in strict runner"
            claim_role = "primary"
        elif row["ran_pipeline"] == "True":
            provenance = "machine artifact shows pipeline was run; exploratory/comparator endpoint"
            claim_role = "exploratory_or_comparator"
        else:
            provenance = "available in constructed artifacts but not part of reported retrospective POC"
            claim_role = "not_reported_primary"
        ledger.append(
            {
                "endpoint_name": endpoint,
                "available_in_raw_or_rebuilt": row["available_in_raw"],
                "available_in_constructed_surface": row["available_in_constructed_surface"],
                "ran_pipeline": row["ran_pipeline"],
                "claim_role": claim_role,
                "eligible_surface_count": row["eligible_surface_count"],
                "mean_hidden_BA": row["mean_hidden_BA"],
                "mean_lift": row["mean_lift"],
                "reported_in_primary_poc": str(endpoint == "acceptable_floor_choice"),
                "provenance_status": provenance,
                "evidence_source": "results/full_repro/endpoint_audit_table.csv",
            }
        )
    write_csv(
        OUT_CSV,
        [
            "endpoint_name",
            "available_in_raw_or_rebuilt",
            "available_in_constructed_surface",
            "ran_pipeline",
            "claim_role",
            "eligible_surface_count",
            "mean_hidden_BA",
            "mean_lift",
            "reported_in_primary_poc",
            "provenance_status",
            "evidence_source",
        ],
        ledger,
    )

    md = [
        "# Endpoint Attempt Ledger",
        "",
        "This ledger is generated from machine-readable endpoint audit artifacts, not README prose.",
        "",
        "Key interpretation:",
        "- `acceptable_floor_choice` is the reported retrospective dense-posture POC endpoint.",
        "- Other endpoint rows disclose available/exploratory/comparator endpoint attempts where machine artifacts exist.",
        "- This ledger does not prove AFC was prechosen unless separate dated planning records are supplied.",
        "",
        "| Endpoint | Ran pipeline | Role | Eligible surfaces | Mean BA | Lift |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for row in ledger:
        md.append(
            f"| `{row['endpoint_name']}` | {row['ran_pipeline']} | {row['claim_role']} | "
            f"{row['eligible_surface_count']} | {row['mean_hidden_BA']} | {row['mean_lift']} |"
        )
    OUT_MD.write_text("\n".join(md))

    endpoints = {row["endpoint_name"] for row in ledger}
    required = {
        "acceptable_floor_choice",
        "below_floor",
        "clean_harmful_undertriage",
        "floor_vs_ceiling_within_range_only",
        "outside_range",
    }
    missing = required - endpoints
    if missing:
        raise SystemExit(f"Endpoint ledger missing expected endpoints: {sorted(missing)}")
    if not any(row["endpoint_name"] == "acceptable_floor_choice" and row["reported_in_primary_poc"] == "True" for row in ledger):
        raise SystemExit("Endpoint ledger does not mark AFC as reported POC endpoint")
    print(f"Endpoint attempt ledger written for {len(ledger)} endpoints.")


if __name__ == "__main__":
    main()
