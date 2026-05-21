#!/usr/bin/env python3
"""Rebuild the cross-model trial-level raw extract from original results.json files."""

from __future__ import annotations

import csv
import gzip
import json
from collections import Counter

from full_repro_common import (
    CROSS_MODEL_METADATA_SOURCE,
    FULL_AUDIT,
    FULL_RESULTS,
    JSON_INFERENCE_ROOT,
    RAW_TRIAL_SOURCE,
    WORKBENCH_TRIAL_EXTRACT_SOURCE,
    read_csv_stream,
    write_csv,
)


FIELDS = [
    "model",
    "temperature",
    "is_reasoning_model",
    "problem_idx",
    "case_id",
    "variant_code",
    "trial_idx",
    "extracted_answer",
    "is_correct",
    "gold_triage",
    "is_edge_case",
    "triage_boundary",
    "acuity",
    "domain",
    "diagnosis",
    "scenario_num",
    "case_pair",
    "race",
    "gender",
    "has_anchor",
    "anchor_type",
    "has_barrier",
    "barrier_type",
    "prompt_type",
    "case_num",
    "variant_num",
    "raw_output",
]

REASONING_MODELS = {"gpt-5-mini", "gpt-5.4-thinking"}


def model_params(model: str) -> tuple[str, str]:
    if model in REASONING_MODELS:
        return "", "True"
    return "0.6", "False"


def bool_text(value: object) -> str:
    return "True" if bool(value) else "False"


def build_rows():
    metadata = list(csv.DictReader(CROSS_MODEL_METADATA_SOURCE.open(newline="")))
    model_dirs = sorted(p for p in JSON_INFERENCE_ROOT.iterdir() if p.is_dir())
    for model_dir in model_dirs:
        model = model_dir.name
        temperature, is_reasoning = model_params(model)
        for idx, meta in enumerate(metadata):
            path = model_dir / f"problem_{idx}" / "results.json"
            if not path.exists():
                raise SystemExit(f"Missing JSON result: {path}")
            obj = json.loads(path.read_text())
            trials = obj.get("trials", [])
            if len(trials) != 10:
                raise SystemExit(f"Expected 10 trials in {path}; found {len(trials)}")
            for trial in trials:
                yield {
                    "model": model,
                    "temperature": temperature,
                    "is_reasoning_model": is_reasoning,
                    "problem_idx": idx,
                    "case_id": meta["case_id"],
                    "variant_code": meta["variant_code"],
                    "trial_idx": trial.get("trial_idx", ""),
                    "extracted_answer": trial.get("extracted_answer") or "",
                    "is_correct": bool_text(trial.get("is_correct")),
                    "gold_triage": meta["gold_triage"],
                    "is_edge_case": meta["is_edge_case"],
                    "triage_boundary": meta["triage_boundary"],
                    "acuity": meta["acuity"],
                    "domain": meta["domain"],
                    "diagnosis": meta["diagnosis"],
                    "scenario_num": meta["scenario_num"],
                    "case_pair": meta["case_pair"],
                    "race": meta["race"],
                    "gender": meta["gender"],
                    "has_anchor": meta["has_anchor"],
                    "anchor_type": meta["anchor_type"],
                    "has_barrier": meta["has_barrier"],
                    "barrier_type": meta["barrier_type"],
                    "prompt_type": meta["prompt_type"],
                    "case_num": meta["case_num"],
                    "variant_num": meta["variant_num"],
                    "raw_output": trial.get("raw_output") or "",
                }


def compare_to_workbench() -> tuple[int, int, Counter, list[dict[str, object]]]:
    generated = {
        (row["model"], row["problem_idx"], row["trial_idx"]): row
        for row in read_csv_stream(RAW_TRIAL_SOURCE)
    }
    frozen = {
        (row["model"], row["problem_idx"], row["trial_idx"]): row
        for row in read_csv_stream(WORKBENCH_TRIAL_EXTRACT_SOURCE)
    }
    mismatch_rows: list[dict[str, object]] = []
    field_counts: Counter = Counter()
    for key in sorted(set(generated) | set(frozen)):
        left = generated.get(key)
        right = frozen.get(key)
        if left is None or right is None:
            field = "row_presence"
            field_counts[field] += 1
            mismatch_rows.append(
                {
                    "model": key[0],
                    "problem_idx": key[1],
                    "trial_idx": key[2],
                    "field": field,
                    "generated_value": "present" if left else "missing",
                    "workbench_value": "present" if right else "missing",
                }
            )
            continue
        for field in FIELDS:
            if str(left[field]) != str(right[field]):
                field_counts[field] += 1
                if len(mismatch_rows) < 1000:
                    mismatch_rows.append(
                        {
                            "model": key[0],
                            "problem_idx": key[1],
                            "trial_idx": key[2],
                            "field": field,
                            "generated_value": left[field],
                            "workbench_value": right[field],
                        }
                    )
    return len(generated), len(frozen), field_counts, mismatch_rows


def main() -> None:
    RAW_TRIAL_SOURCE.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(RAW_TRIAL_SOURCE, "wt", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for row in build_rows():
            writer.writerow(row)

    generated_n, frozen_n, field_counts, mismatch_rows = compare_to_workbench()
    write_csv(
        FULL_RESULTS / "json_trial_extract_mismatches.csv",
        ["model", "problem_idx", "trial_idx", "field", "generated_value", "workbench_value"],
        mismatch_rows,
    )

    report = [
        "# JSON Trial Extract Rebuild Report",
        "",
        f"Generated trial rows: {generated_n}",
        f"Workbench trial rows: {frozen_n}",
        f"Mismatch rows retained: {len(mismatch_rows)}",
        f"Total mismatched field values: {sum(field_counts.values())}",
        "",
        "Field mismatch counts:",
    ]
    if field_counts:
        for field, count in sorted(field_counts.items()):
            report.append(f"- {field}: {count}")
    else:
        report.append("- none")
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    (FULL_AUDIT / "json_rebuild_vs_workbench_trial_extract_report.md").write_text("\n".join(report))
    if generated_n != 86400 or frozen_n != 86400 or field_counts:
        raise SystemExit("JSON trial extract rebuild did not exactly match workbench trial extract")
    print("Rebuilt cross-model trial extract from 8,640 JSON files and matched the workbench extract exactly.")


if __name__ == "__main__":
    main()
