# Parser Replay Report

Total raw responses parsed: 87360
Parser success rate: 0.994631
Parser failure count: 469
Ambiguous responses: not separately classified by this frozen parser
Manual overrides: 0
Override rule: none; GPT-Health uses structured `llm_triage` because its package-local `response_raw` field is not a free-text model-answer field
Exact parser version: 2026-05-20.full-repro-draft
Source extracted-answer disagreements: 0

Rule counts:
- answer_like_field: 27
- empty: 241
- last_single_letter: 954
- no_match: 228
- source_structured_llm_triage: 960
- standalone_line: 26
- triage_field: 84924