#!/usr/bin/env python3
"""Executable replay of the 0.525086 majority-baseline anomaly."""

from __future__ import annotations

import csv

from full_repro_common import FULL_AUDIT, FULL_RESULTS, mean, write_csv


SPLIT_METRICS = FULL_RESULTS / "split_level_metrics.csv"
ONE_CLASS_OUT = FULL_RESULTS / "one_class_hidden_split_table.csv"


def main() -> None:
    rows = list(csv.DictReader(SPLIT_METRICS.open(newline="")))
    both = [r for r in rows if int(r["hidden_positive"]) > 0 and int(r["hidden_negative"]) > 0]
    only_pos = [r for r in rows if int(r["hidden_positive"]) > 0 and int(r["hidden_negative"]) == 0]
    only_neg = [r for r in rows if int(r["hidden_positive"]) == 0 and int(r["hidden_negative"]) > 0]
    split_pooled_majority = mean(float(r["majority_ba"]) for r in rows)
    models = sorted({r["model_name"] for r in rows})
    implemented_majority = mean(
        mean(float(r["majority_ba"]) for r in rows if r["model_name"] == model)
        for model in models
    )
    strict_two_class_majority = mean(
        mean(float(r["majority_ba"]) for r in both if r["model_name"] == model)
        for model in models
    )
    sensitivity_degree1 = mean(
        mean(float(r["degree1_ba"]) for r in both if r["model_name"] == model)
        for model in models
    )
    sensitivity_lift = mean(
        mean(float(r["degree1_ba"]) - float(r["majority_ba"]) for r in both if r["model_name"] == model)
        for model in models
    )

    out_rows = [
        {
            "case": "both_classes",
            "split_count": len(both),
            "balanced_accuracy_rule": "average positive and negative recall",
        },
        {
            "case": "only_positives",
            "split_count": len(only_pos),
            "balanced_accuracy_rule": "positive recall only",
        },
        {
            "case": "only_negatives",
            "split_count": len(only_neg),
            "balanced_accuracy_rule": "negative recall only",
        },
    ]
    write_csv(ONE_CLASS_OUT, ["case", "split_count", "balanced_accuracy_rule"], out_rows)

    report = [
        "# Metric Anomaly Replay",
        "",
        f"Number of hidden splits with both classes: {len(both)}",
        f"Number of hidden splits with only positives: {len(only_pos)}",
        f"Number of hidden splits with only negatives: {len(only_neg)}",
        "",
        "Balanced accuracy rule:",
        "- Hidden set has both classes: average positive and negative recall.",
        "- Hidden set has only positives: use positive recall only.",
        "- Hidden set has only negatives: use negative recall only.",
        "",
        f"Majority baseline under implemented primary aggregation: {implemented_majority:.12f}",
        f"Majority baseline under split-pooled aggregation: {split_pooled_majority:.12f}",
        "Theoretical binary constant baseline when both classes are present: 0.500000",
        f"Majority baseline after excluding one-class hidden splits: {strict_two_class_majority:.12f}",
        f"Degree-1 BA after excluding one-class hidden splits: {sensitivity_degree1:.12f}",
        f"Degree-1 lift after excluding one-class hidden splits: {sensitivity_lift:.12f}",
        "",
        "The implemented majority baseline is above 0.500 because split-level balanced accuracy is averaged after applying the available-class rule to one-class hidden splits.",
    ]
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    (FULL_AUDIT / "metric_anomaly_replay.md").write_text("\n".join(report))
    print("Wrote executable metric anomaly replay.")


if __name__ == "__main__":
    main()
