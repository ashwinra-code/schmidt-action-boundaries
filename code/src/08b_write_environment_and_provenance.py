#!/usr/bin/env python3
"""Write environment report and provenance ledger for generated full-repro outputs."""

from __future__ import annotations

import csv
import platform
import subprocess
import sys
from datetime import datetime, timezone

from full_repro_common import FULL_AUDIT, FULL_RESULTS, FULL_SPLITS, PKG_ROOT, sha256, write_csv


LEDGER_OUT = FULL_AUDIT / "provenance_ledger.csv"
ENV_OUT = FULL_AUDIT / "environment_report.md"


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=PKG_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "not_a_git_repository"


def main() -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    entries = [
        ("raw_input", PKG_ROOT / "data" / "raw" / "raw_input_manifest.csv", "manual_manifest", "", ""),
        ("parsed_response", FULL_RESULTS / "parsed_responses.csv", "src/01_parse_raw_responses.py", "raw inputs", ""),
        ("afc_cell_table", FULL_RESULTS / "afc_cell_table_from_raw.csv", "src/02_build_afc_cell_table.py", "parsed_responses.csv", ""),
        ("surface_table", FULL_RESULTS / "surface_assembly_table.csv", "src/03_assemble_surfaces.py", "afc_cell_table_from_raw.csv", ""),
        ("eligibility_table", FULL_RESULTS / "denominator_table.csv", "src/04_denominator_and_eligibility.py", "surface_assembly_table.csv", ""),
        ("split_manifest", FULL_SPLITS / "q12_split_manifest.csv", "src/05_generate_or_replay_split_masks.py", "data/canonical/afc_q12_split_membership_index.csv", "replayed locked manifest"),
        ("hidden_predictions", FULL_RESULTS / "hidden_predictions.csv", "src/06_fit_and_score_reconstructors.py", "afc cells and split manifest", ""),
        ("main_metrics", FULL_RESULTS / "main_result_table.csv", "src/06_fit_and_score_reconstructors.py", "split_level_metrics.csv", ""),
        ("null_distribution", FULL_RESULTS / "null_distribution.csv", "src/07_run_baselines_and_nulls.py", "raw-built AFC labels and original null split rule", "raw recomputed"),
        ("null_permutation_manifest", FULL_RESULTS / "null_permutation_manifest.csv", "src/07_run_baselines_and_nulls.py", "raw-built AFC labels", "permutation hashes"),
        ("robustness_outputs", FULL_RESULTS / "single_axis_dominance_table.csv", "src/08_sensitivity_and_robustness.py", "afc cells and split metrics", ""),
    ]
    rows = []
    for stage, path, script, inputs, notes in entries:
        rows.append(
            {
                "stage": stage,
                "file_path": str(path.relative_to(PKG_ROOT) if path.is_relative_to(PKG_ROOT) else path),
                "sha256": sha256(path) if path.exists() else "",
                "generated_by_script": script,
                "input_files": inputs,
                "timestamp": timestamp,
                "notes": notes,
            }
        )
    write_csv(
        LEDGER_OUT,
        ["stage", "file_path", "sha256", "generated_by_script", "input_files", "timestamp", "notes"],
        rows,
    )

    report = [
        "# Environment Report",
        "",
        f"OS: {platform.platform()}",
        f"Python version: {sys.version.split()[0]}",
        "Package versions: Python stdlib plus NumPy for vectorized null recomputation",
        f"Git commit: {git_commit()}",
        f"Artifact hashes: see `audit/full_repro/provenance_ledger.csv`",
        "Runtime: not benchmarked",
    ]
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    ENV_OUT.write_text("\n".join(report))
    print("Wrote environment report and provenance ledger.")


if __name__ == "__main__":
    main()
