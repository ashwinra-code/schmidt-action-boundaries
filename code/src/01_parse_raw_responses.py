#!/usr/bin/env python3
"""Replay the frozen triage parser against raw-response artifacts."""

from __future__ import annotations

from collections import Counter

from full_repro_common import (
    FULL_AUDIT,
    FULL_RESULTS,
    GPT_HEALTH_RAW_SOURCE,
    PKG_ROOT,
    RAW_TRIAL_SOURCE,
    TRIAGE_ORD,
    classify_prediction,
    extract_triage_letter,
    read_csv_stream,
    write_csv,
)


OUT = FULL_RESULTS / "parsed_responses.csv"

FIELDS = [
    "response_id",
    "model_name",
    "model_snapshot",
    "vignette_id",
    "condition_id",
    "trial_idx",
    "raw_response_text",
    "parsed_triage_label",
    "parsed_action_label",
    "acceptable_floor_choice",
    "below_floor",
    "outside_range",
    "clean_harmful_undertriage",
    "parser_rule_id",
    "parser_confidence_or_flag",
    "parser_error_flag",
    "source_extracted_answer",
    "gold_triage",
    "scenario_id",
    "case_id",
    "variant_code",
    "race",
    "gender",
    "has_anchor",
    "has_barrier",
    "diagnosis",
    "domain",
]


def parse_cross_model_rows():
    for row in read_csv_stream(RAW_TRIAL_SOURCE):
        raw_text = row.get("raw_output", "")
        label, rule = extract_triage_letter(raw_text)
        endpoint = classify_prediction(label, row["gold_triage"])
        yield {
            "response_id": f"{row['model']}|problem_{row['problem_idx']}|trial_{row['trial_idx']}",
            "model_name": row["model"],
            "model_snapshot": row["model"],
            "vignette_id": f"problem_{row['problem_idx']}",
            "condition_id": row.get("variant_code", ""),
            "trial_idx": row["trial_idx"],
            "raw_response_text": raw_text,
            "parsed_triage_label": label or "",
            "parsed_action_label": label or "",
            "acceptable_floor_choice": endpoint["acceptable_floor_choice"],
            "below_floor": endpoint["below_floor"],
            "outside_range": endpoint["outside_range"],
            "clean_harmful_undertriage": "",
            "parser_rule_id": rule,
            "parser_confidence_or_flag": "deterministic_regex",
            "parser_error_flag": int(label not in TRIAGE_ORD),
            "source_extracted_answer": row.get("extracted_answer", ""),
            "gold_triage": row["gold_triage"],
            "scenario_id": row["scenario_num"],
            "case_id": row["case_id"],
            "variant_code": row["variant_code"],
            "race": row["race"],
            "gender": row["gender"],
            "has_anchor": row["has_anchor"],
            "has_barrier": row["has_barrier"],
            "diagnosis": row["diagnosis"],
            "domain": row["domain"],
        }


def parse_gpt_health_rows():
    for idx, row in enumerate(read_csv_stream(GPT_HEALTH_RAW_SOURCE)):
        raw_text = row.get("response_raw", "")
        label = row.get("llm_triage", "").strip().upper()
        rule = "source_structured_llm_triage"
        endpoint = classify_prediction(label, row["gold_triage"])
        yield {
            "response_id": f"gpt-health|row_{idx}",
            "model_name": "gpt-health",
            "model_snapshot": "gpt-health",
            "vignette_id": f"problem_{idx}",
            "condition_id": row.get("variant_code", ""),
            "trial_idx": 0,
            "raw_response_text": raw_text,
            "parsed_triage_label": label or "",
            "parsed_action_label": label or "",
            "acceptable_floor_choice": endpoint["acceptable_floor_choice"],
            "below_floor": endpoint["below_floor"],
            "outside_range": endpoint["outside_range"],
            "clean_harmful_undertriage": "",
            "parser_rule_id": rule,
            "parser_confidence_or_flag": "structured_source_field",
            "parser_error_flag": int(label not in TRIAGE_ORD),
            "source_extracted_answer": row.get("llm_triage", ""),
            "gold_triage": row["gold_triage"],
            "scenario_id": row["scenario_num"],
            "case_id": row["case_id"],
            "variant_code": row["variant_code"],
            "race": row["race"],
            "gender": row["gender"],
            "has_anchor": row["has_anchor"],
            "has_barrier": row["has_barrier"],
            "diagnosis": row["diagnosis"],
            "domain": row["domain"],
        }


def main() -> None:
    counters = Counter()

    def rows():
        for parsed in parse_cross_model_rows():
            counters["total"] += 1
            counters[f"rule:{parsed['parser_rule_id']}"] += 1
            counters["failures"] += int(parsed["parser_error_flag"])
            if parsed["source_extracted_answer"] and parsed["source_extracted_answer"] != parsed["parsed_triage_label"]:
                counters["source_extracted_answer_disagreements"] += 1
            yield parsed
        for parsed in parse_gpt_health_rows():
            counters["total"] += 1
            counters[f"rule:{parsed['parser_rule_id']}"] += 1
            counters["failures"] += int(parsed["parser_error_flag"])
            if parsed["source_extracted_answer"] and parsed["source_extracted_answer"] != parsed["parsed_triage_label"]:
                counters["source_extracted_answer_disagreements"] += 1
            yield parsed

    write_csv(OUT, FIELDS, rows())

    report = [
        "# Parser Replay Report",
        "",
        f"Total raw responses parsed: {counters['total']}",
        f"Parser success rate: {(1 - counters['failures'] / counters['total']):.6f}",
        f"Parser failure count: {counters['failures']}",
        "Ambiguous responses: not separately classified by this frozen parser",
        "Manual overrides: 0",
        "Override rule: none; GPT-Health uses structured `llm_triage` because its package-local `response_raw` field is not a free-text model-answer field",
        "Exact parser version: 2026-05-20.full-repro-draft",
        f"Source extracted-answer disagreements: {counters['source_extracted_answer_disagreements']}",
        "",
        "Rule counts:",
    ]
    for key, value in sorted(counters.items()):
        if key.startswith("rule:"):
            report.append(f"- {key[5:]}: {value}")
    FULL_AUDIT.mkdir(parents=True, exist_ok=True)
    (FULL_AUDIT / "parser_replay_report.md").write_text("\n".join(report))
    print(f"Parsed {counters['total']} raw responses into {OUT.relative_to(PKG_ROOT)}")


if __name__ == "__main__":
    main()
