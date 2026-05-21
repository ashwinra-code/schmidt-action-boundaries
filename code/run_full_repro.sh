#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$(basename "$SCRIPT_DIR")" == "code" ]]; then
  CAPSULE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
  PY_SRC="code/src"
else
  CAPSULE_ROOT="$SCRIPT_DIR"
  PY_SRC="src"
fi
cd "$CAPSULE_ROOT"

run_py() {
  local script="$1"
  shift
  python3 "$PY_SRC/$script" "$@"
}

MODE="--strict"
CLEAN="1"
for arg in "$@"; do
  case "$arg" in
    --strict|--allow-frozen-null|--preflight)
      MODE="$arg"
      ;;
    --clean)
      CLEAN="1"
      ;;
    --no-clean)
      CLEAN="0"
      ;;
    *)
      echo "Usage: bash code/run_full_repro.sh [--preflight|--strict|--allow-frozen-null] [--clean|--no-clean]" >&2
      exit 2
      ;;
  esac
done

if [[ "$MODE" != "--preflight" && "$MODE" != "--strict" && "$MODE" != "--allow-frozen-null" ]]; then
  echo "Usage: bash code/run_full_repro.sh [--preflight|--strict|--allow-frozen-null] [--clean|--no-clean]" >&2
  exit 2
fi

echo "STRICT RAW-RESPONSE-TO-RESULT RETROSPECTIVE POC REPRODUCTION"

run_py "00_validate_raw_inputs.py"
if [[ "$MODE" == "--preflight" ]]; then
  echo "PREFLIGHT PASSED"
  exit 0
fi

if [[ "$CLEAN" == "1" ]]; then
  rm -rf results/full_repro
  rm -rf audit/full_repro
  rm -rf data/splits/full_repro
fi

mkdir -p results/full_repro
mkdir -p audit/full_repro
mkdir -p data/splits/full_repro

if [[ "$MODE" == "--strict" ]]; then
  export STRICT_REPRO_MODE=1
else
  unset STRICT_REPRO_MODE
fi

run_py "00_validate_raw_inputs.py"
run_py "00b_build_trial_extract_from_json.py"
run_py "01_parse_raw_responses.py"
run_py "02_build_afc_cell_table.py"
run_py "03_assemble_surfaces.py"
run_py "03b_compare_rebuilt_to_canonical_artifacts.py"
run_py "04_denominator_and_eligibility.py"
run_py "05_generate_or_replay_split_masks.py"
run_py "06_fit_and_score_reconstructors.py"
run_py "06b_metric_anomaly_replay.py"
run_py "07_run_baselines_and_nulls.py"
run_py "08_sensitivity_and_robustness.py"
run_py "08b_write_environment_and_provenance.py"
run_py "11_build_endpoint_attempt_ledger.py"
run_py "12_build_handoff_manifest.py"
if [[ "$MODE" == "--allow-frozen-null" ]]; then
  run_py "09_assert_final_reproduction.py" --mode allow-frozen-null
else
  run_py "09_assert_final_reproduction.py" --mode strict
fi
run_py "10_clean_environment_probe.py"

echo "FULL REPRO PASSED"
