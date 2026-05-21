#!/usr/bin/env python3
"""Shared helpers for the retrospective AFC raw-response replay pipeline."""

from __future__ import annotations

import csv
import gzip
import hashlib
import math
import os
import re
from collections import Counter
from pathlib import Path
from typing import Iterable


SRC_ROOT = Path(__file__).resolve().parent
if SRC_ROOT.parent.name == "code":
    PKG_ROOT = SRC_ROOT.parent.parent
    CODE_ROOT = SRC_ROOT.parent
else:
    PKG_ROOT = SRC_ROOT.parent
    CODE_ROOT = PKG_ROOT

STRICT_REPRO_MODE = os.environ.get("STRICT_REPRO_MODE") == "1"
EXPECTED_OUTPUT_ROOTS = (
    PKG_ROOT / "results" / "expected",
    PKG_ROOT / "audit" / "expected",
)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _is_read_mode(mode: str) -> bool:
    return "r" in mode or "+" in mode


def guard_computational_input(path: Path) -> None:
    """Block strict-mode computational reads from shipped expected outputs."""
    if not STRICT_REPRO_MODE:
        return
    resolved = path.expanduser().resolve()
    for root in EXPECTED_OUTPUT_ROOTS:
        if _is_relative_to(resolved, root.resolve()):
            raise RuntimeError(
                "Strict reproduction code may not read shipped expected outputs "
                f"as computational inputs: {resolved}"
            )


_ORIGINAL_PATH_OPEN = Path.open


def _guarded_path_open(
    self: Path,
    mode: str = "r",
    buffering: int = -1,
    encoding: str | None = None,
    errors: str | None = None,
    newline: str | None = None,
):
    if _is_read_mode(mode):
        guard_computational_input(self)
    return _ORIGINAL_PATH_OPEN(self, mode, buffering, encoding, errors, newline)


Path.open = _guarded_path_open


def env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    if value:
        return Path(value).expanduser().resolve()
    return default.resolve()


DATA_ROOT = env_path("REPRO_DATA_ROOT", PKG_ROOT / "data")
RAW_ROOT = env_path("REPRO_RAW_ROOT", DATA_ROOT / "raw" / "source_artifacts")
CANONICAL_ROOT = env_path("REPRO_CANONICAL_ROOT", DATA_ROOT / "canonical")
SPECS_ROOT = DATA_ROOT / "specs" if (DATA_ROOT / "specs").exists() else PKG_ROOT / "specs"

FULL_RESULTS = PKG_ROOT / "results" / "full_repro"
FULL_AUDIT = PKG_ROOT / "audit" / "full_repro"
FULL_SPLITS = PKG_ROOT / "data" / "splits" / "full_repro"
RAW_TRIAL_SOURCE = (
    FULL_RESULTS / "cross_model_trial_raw_extract_from_json.csv.gz"
)
WORKBENCH_TRIAL_EXTRACT_SOURCE = CANONICAL_ROOT / "trial_level_long_with_raw.csv.gz"
JSON_INFERENCE_ROOT = RAW_ROOT / "cross_model" / "inference"
CROSS_MODEL_METADATA_SOURCE = RAW_ROOT / "cross_model" / "DataOriginal_FINAL.csv"
GPT_HEALTH_RAW_SOURCE = RAW_ROOT / "gpt_health" / "DataOriginal_FINAL.csv"

CANONICAL_FULL_CELL_SOURCE = CANONICAL_ROOT / "full_cell_table_constructed.csv"
CANONICAL_SPLIT_SOURCE = CANONICAL_ROOT / "afc_q12_split_membership_index.csv"
CANONICAL_ADJUDICATED_SUMMARY = CANONICAL_ROOT / "posture_primary_summary.csv"
CANONICAL_PER_MODEL = CANONICAL_ROOT / "posture_primary_balanced_degree1_vs_baselines.csv"
CANONICAL_ENDPOINT_DENOMS = CANONICAL_ROOT / "model_endpoint_denominators.csv"
CANONICAL_SHUFFLE_SUMMARY = CANONICAL_ROOT / "label_shuffle_distribution_summary.csv"
CANONICAL_SHUFFLE_REPLICATES = CANONICAL_ROOT / "label_shuffle_distribution_replicates.csv"
CANONICAL_COMPARATORS = CANONICAL_ROOT / "comparator_metrics.csv"
CANONICAL_BUDGET_CURVE = CANONICAL_ROOT / "budget_curve_bootstrap_ci.csv"
CANONICAL_HAMMING_DEPTH = CANONICAL_ROOT / "hamming_depth_summary.csv"
CANONICAL_ENDPOINT_AUDIT = CANONICAL_ROOT / "endpoint_audit_table.csv"

AXES = ["anchor", "access", "black", "woman", "objective"]
TRIAGE_ORD = {"A": 1, "B": 2, "C": 3, "D": 4}
ORD_TRIAGE = {v: k for k, v in TRIAGE_ORD.items()}


def read_csv(path: Path) -> list[dict[str, str]]:
    guard_computational_input(path)
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_csv_stream(path: Path) -> Iterable[dict[str, str]]:
    guard_computational_input(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", newline="") as f:
        yield from csv.DictReader(f)


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def copy_csv(src: Path, dst: Path, filter_fn=None) -> int:
    guard_computational_input(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with src.open(newline="") as f_in, dst.open("w", newline="") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames or [])
        writer.writeheader()
        for row in reader:
            if filter_fn is None or filter_fn(row):
                writer.writerow(row)
                count += 1
    return count


def sha256(path: Path) -> str:
    guard_computational_input(path)
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_row_count(path: Path) -> int:
    return sum(1 for _ in read_csv_stream(path))


def extract_triage_letter(text: str | None) -> tuple[str | None, str]:
    if not text:
        return None, "empty"
    patterns = [
        (r"TRIAGE[:\s]*([A-D])\b", "triage_field"),
        (r"\\boxed\{([A-D])\}", "boxed"),
        (r"(?:answer|recommendation|category)[:\s]*([A-D])\b", "answer_like_field"),
        (r"^\s*([A-D])\s*$", "standalone_line"),
    ]
    for pattern, rule_id in patterns:
        flags = re.IGNORECASE | (re.MULTILINE if rule_id == "standalone_line" else 0)
        m = re.search(pattern, text, flags)
        if m:
            return m.group(1).upper(), rule_id
    matches = re.findall(r"\b([A-D])\b", text)
    if matches:
        return matches[-1].upper(), "last_single_letter"
    return None, "no_match"


def gold_bounds(gold: str) -> tuple[int, int]:
    vals: list[int] = []
    for token in str(gold).replace("/", " ").split():
        tri = token.strip().upper()
        if tri in TRIAGE_ORD:
            vals.append(TRIAGE_ORD[tri])
    if not vals:
        raise ValueError(f"Cannot parse gold triage {gold!r}")
    return min(vals), max(vals)


def classify_prediction(label: str | None, gold_triage: str) -> dict[str, object]:
    lo, hi = gold_bounds(gold_triage)
    if label not in TRIAGE_ORD:
        return {
            "pred_ord": "",
            "below_floor": "",
            "outside_range": "",
            "acceptable_floor_choice": "",
        }
    po = TRIAGE_ORD[label]
    within = lo <= po <= hi
    return {
        "pred_ord": po,
        "below_floor": int(po < lo),
        "outside_range": int(not within),
        "acceptable_floor_choice": int((lo < hi) and (po == lo)),
    }


def axes_from_source_row(row: dict[str, str]) -> dict[str, int]:
    return {
        "anchor": int(str(row.get("has_anchor", "")).lower() == "yes"),
        "access": int(str(row.get("has_barrier", "")).lower() == "yes"),
        "black": int(str(row.get("race", "")).lower() == "black"),
        "woman": int(str(row.get("gender", "")).lower() == "woman"),
        "objective": int(bool(re.match(r"^(E|MH)", str(row.get("case_id", ""))))),
    }


def cell_id_from_axes(values: dict[str, int]) -> int:
    return sum(int(values[axis]) * (2**idx) for idx, axis in enumerate(AXES))


def axes_from_cell_id(cell_id: int) -> dict[str, int]:
    return {axis: (int(cell_id) >> idx) & 1 for idx, axis in enumerate(AXES)}


def degree1_features(cell_id: int) -> list[float]:
    axes = axes_from_cell_id(cell_id)
    return [1.0] + [2.0 * axes[a] - 1.0 for a in AXES]


def solve_linear_system(a: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    mat = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(mat[r][col]))
        if abs(mat[pivot][col]) < 1e-12:
            raise ValueError("Singular ridge system")
        if pivot != col:
            mat[col], mat[pivot] = mat[pivot], mat[col]
        div = mat[col][col]
        mat[col] = [v / div for v in mat[col]]
        for row in range(n):
            if row == col:
                continue
            factor = mat[row][col]
            if factor:
                mat[row] = [v - factor * mat[col][i] for i, v in enumerate(mat[row])]
    return [mat[i][-1] for i in range(n)]


def ridge_scores(
    observed_cell_ids: list[int],
    observed_labels: list[int],
    predict_cell_ids: list[int],
    ridge_lambda: float = 1.0,
) -> list[float]:
    if len(set(observed_labels)) == 1:
        return [float(observed_labels[0])] * len(predict_cell_ids)

    p = 6
    xtx = [[0.0 for _ in range(p)] for _ in range(p)]
    xty = [0.0 for _ in range(p)]
    for cell_id, y in zip(observed_cell_ids, observed_labels):
        x = degree1_features(cell_id)
        for i in range(p):
            xty[i] += x[i] * float(y)
            for j in range(p):
                xtx[i][j] += x[i] * x[j]
    penalties = [1e-9] + [ridge_lambda] * (p - 1)
    for i, penalty in enumerate(penalties):
        xtx[i][i] += penalty
    beta = solve_linear_system(xtx, xty)
    scores = []
    for cell_id in predict_cell_ids:
        x = degree1_features(cell_id)
        score = sum(beta[i] * x[i] for i in range(p))
        scores.append(min(1.0, max(0.0, score)))
    return scores


def balanced_accuracy(true_labels: list[int], pred_labels: list[int]) -> float:
    recalls = []
    for cls in [1, 0]:
        denom = sum(1 for y in true_labels if y == cls)
        if denom:
            num = sum(1 for y, pred in zip(true_labels, pred_labels) if y == cls and pred == cls)
            recalls.append(num / denom)
    if not recalls:
        return math.nan
    return sum(recalls) / len(recalls)


def mean(values: Iterable[float]) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else math.nan


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    pos = (len(ordered) - 1) * pct
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return ordered[lo]
    return ordered[lo] * (hi - pos) + ordered[hi] * (pos - lo)


def modal_answer(labels: list[str]) -> str | None:
    valid = [label for label in labels if label in TRIAGE_ORD]
    if not valid:
        return None
    return Counter(valid).most_common(1)[0][0]
