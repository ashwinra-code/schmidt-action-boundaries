#!/usr/bin/env python3
"""Validate raw input files for the retrospective AFC replay."""

from __future__ import annotations

import csv
import gzip
import hashlib
from pathlib import Path

from full_repro_common import FULL_AUDIT, PKG_ROOT, csv_row_count, sha256


MANIFEST = PKG_ROOT / "data" / "raw" / "raw_input_manifest.csv"
PREFLIGHT_AUDIT = PKG_ROOT / "audit" / "preflight"

REQUIRED_COLUMNS = {
    "cross_model_metadata_csv": {
        "case_num",
        "case_id",
        "variant_num",
        "domain",
        "diagnosis",
        "gold_triage",
        "triage_boundary",
        "acuity",
        "variant_code",
        "race",
        "gender",
        "anchor_type",
        "barrier_type",
        "prompt_type",
        "case_pair",
        "scenario_num",
        "has_anchor",
        "has_barrier",
        "is_edge_case",
    },
    "cross_model_trial_raw_extract": {
        "model",
        "problem_idx",
        "case_id",
        "variant_code",
        "trial_idx",
        "extracted_answer",
        "gold_triage",
        "raw_output",
        "race",
        "gender",
        "has_anchor",
        "has_barrier",
        "scenario_num",
        "diagnosis",
        "domain",
    },
    "gpt_health_original_raw_csv": {
        "case_num",
        "case_id",
        "variant_num",
        "diagnosis",
        "domain",
        "gold_triage",
        "variant_code",
        "race",
        "gender",
        "prompt_text",
        "response_raw",
        "llm_triage",
        "scenario_num",
        "has_anchor",
        "has_barrier",
        "is_edge_case",
    },
}


def tree_sha256(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    count = 0
    for item in sorted(path.rglob("results.json")):
        rel = item.relative_to(path).as_posix()
        file_hash = sha256(item)
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update(file_hash.encode("utf-8"))
        h.update(b"\n")
        count += 1
    return h.hexdigest(), count


def fieldnames(path: Path) -> list[str]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or [])


def manifest_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (PKG_ROOT / path).resolve()


def main() -> None:
    if not MANIFEST.exists():
        raise SystemExit(f"Missing raw input manifest: {MANIFEST}")

    rows = list(csv.DictReader(MANIFEST.open(newline="")))
    report = ["# Raw Input Validation", ""]
    failures: list[str] = []
    passed = 0

    for row in rows:
        raw_id = row["raw_file_id"]
        path = manifest_path(row["raw_file_path"])
        raw_failures: list[str] = []
        report.append(f"## {raw_id}")
        report.append(f"- Path: `{row['raw_file_path']}`")
        if not path.exists():
            raw_failures.append(f"{raw_id}: missing file {path}")
            report.append("- Status: FAIL, file missing")
            failures.extend(raw_failures)
            continue

        if raw_id == "cross_model_inference_json_tree":
            actual_hash, actual_rows = tree_sha256(path)
            missing_cols = []
        else:
            actual_hash = sha256(path)
            actual_rows = csv_row_count(path)
            cols = set(fieldnames(path))
            missing_cols = sorted(REQUIRED_COLUMNS.get(raw_id, set()) - cols)
        expected_hash = row["sha256"]
        if actual_hash != expected_hash:
            raw_failures.append(f"{raw_id}: sha256 mismatch {actual_hash} != {expected_hash}")
        expected_rows = int(row["expected_rows"])
        if actual_rows != expected_rows:
            raw_failures.append(f"{raw_id}: row count mismatch {actual_rows} != {expected_rows}")
        if missing_cols:
            raw_failures.append(f"{raw_id}: missing columns {missing_cols}")

        if not raw_failures:
            passed += 1
        failures.extend(raw_failures)
        report.append(f"- Rows: {actual_rows}")
        report.append(f"- SHA256: `{actual_hash}`")
        report.append(f"- Missing required columns: {missing_cols if missing_cols else 'none'}")
        report.append("")

    report.append(f"Validated files: {passed} / {len(rows)}")
    PREFLIGHT_AUDIT.mkdir(parents=True, exist_ok=True)
    report_text = "\n".join(report)
    (PREFLIGHT_AUDIT / "raw_input_validation_report.md").write_text(report_text)
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    (FULL_AUDIT / "raw_input_validation_report.md").write_text(report_text)

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(1)
    print(f"Raw input validation passed for {len(rows)} files.")


if __name__ == "__main__":
    main()
