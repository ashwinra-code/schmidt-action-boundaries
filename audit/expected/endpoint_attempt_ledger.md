# Endpoint Attempt Ledger

This ledger is generated from machine-readable endpoint audit artifacts, not README prose.

Key interpretation:
- `acceptable_floor_choice` is the reported retrospective dense-posture POC endpoint.
- Other endpoint rows disclose available/exploratory/comparator endpoint attempts where machine artifacts exist.
- This ledger does not prove AFC was prechosen unless separate dated planning records are supplied.

| Endpoint | Ran pipeline | Role | Eligible surfaces | Mean BA | Lift |
|---|---:|---|---:|---:|---:|
| `acceptable_floor_choice` | True | primary | 77 | 0.74693002007556466 | 0.221843970292014858 |
| `below_floor` | True | exploratory_or_comparator | 11 |  |  |
| `clean_harmful_undertriage` | True | exploratory_or_comparator | 24 |  |  |
| `floor_vs_ceiling_within_range_only` | True | exploratory_or_comparator | 65 | 0.7581899011141713 |  |
| `outside_range` | True | exploratory_or_comparator | 20 |  |  |