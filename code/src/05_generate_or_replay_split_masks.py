#!/usr/bin/env python3
"""Replay frozen q=12 split masks for eligible AFC surfaces."""

from __future__ import annotations

import csv

from full_repro_common import CANONICAL_SPLIT_SOURCE, FULL_AUDIT, FULL_SPLITS, write_csv


OUT = FULL_SPLITS / "q12_split_manifest.csv"
FIELDS = [
    "split_id",
    "surface_id",
    "model_name",
    "scenario_id",
    "seed",
    "q",
    "observed_cell_ids",
    "hidden_cell_ids",
    "mask_generation_rule",
    "used_outcome_labels",
    "used_full_surface_labels",
    "source_rep",
    "source_all_checks_pass",
]


def main() -> None:
    rows = []
    one_class_hidden = 0
    source_rows = 0
    with CANONICAL_SPLIT_SOURCE.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["endpoint"] != "acceptable_floor_choice":
                continue
            if row["query_budget_cells"] != "12":
                continue
            if row["split_design"] != "balanced_random":
                continue
            source_rows += 1
            hidden_floor = int(float(row["recorded_hidden_floor_count"]))
            hidden_ceiling = int(float(row["recorded_hidden_ceiling_count"]))
            if hidden_floor == 0 or hidden_ceiling == 0:
                one_class_hidden += 1
            rows.append(
                {
                    "split_id": f"{row['surface_id']}|q12|balanced_random|rep_{row['rep']}",
                    "surface_id": row["surface_id"],
                    "model_name": row["model"],
                    "scenario_id": row["scenario_pair_id"],
                    "seed": 20260509,
                    "q": 12,
                    "observed_cell_ids": row["Q_cell_ids"],
                    "hidden_cell_ids": row["H_cell_ids"],
                    "mask_generation_rule": "balanced_random: sample q cells without replacement until every design axis has both 0 and 1 represented",
                    "used_outcome_labels": "false",
                    "used_full_surface_labels": "false",
                    "source_rep": row["rep"],
                    "source_all_checks_pass": row["all_checks_pass"],
                }
            )
    write_csv(OUT, FIELDS, rows)

    report = [
        "# Split Mask Report",
        "",
        f"Split rows replayed: {len(rows)}",
        "Query budget q: 12",
        "Mask source: canonical workbench q12 split-membership manifest",
        "Split masks were generated/replayed according to the frozen rule in `data/specs/split_mask_spec.yaml`.",
        "Hidden labels were not used for fitting or hyperparameter selection.",
        "Hidden labels were not used for mask construction by the balanced-random generator in the recovery script.",
        f"One-class hidden splits: {one_class_hidden}",
        f"All source checks pass: {all(r['source_all_checks_pass'] == '1' for r in rows)}",
    ]
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    (FULL_AUDIT / "split_mask_report.md").write_text("\n".join(report))
    if len(rows) != 77000:
        raise SystemExit(f"Expected 77,000 balanced q12 split masks; found {len(rows)}")
    if not all(r["source_all_checks_pass"] == "1" for r in rows):
        raise SystemExit("At least one source split check failed")
    print("Replayed 77,000 q=12 balanced-random split masks.")


if __name__ == "__main__":
    main()
