# Reviewer QA Checklist

## 1. Total Denominator

Answered by: `results/full_repro/denominator_table.csv`

## 2. Eligibility Filter

Answered by: `data/specs/eligibility_rules.yaml` and `audit/full_repro/eligibility_report.md`

## 3. Endpoint Provenance

Answered by: `results/full_repro/endpoint_audit_table.csv`

## 4. q=12 Selection Rule

Answered by: `data/specs/split_mask_spec.yaml` and `data/splits/full_repro/q12_split_manifest.csv`

## 5. Leakage Check

Answered by: `audit/full_repro/split_mask_report.md`

## 6. Reconstructor

Answered by: `data/specs/reconstructor_spec.yaml` and `audit/full_repro/reconstructor_report.md`

## 7. Hyperparameter Isolation

Answered by: `data/specs/reconstructor_spec.yaml`

## 8. 0.525 Baseline Anomaly

Answered by: `audit/full_repro/metric_anomaly_replay.md`

## 9. Aggregation Hierarchy

Answered by: `data/specs/metric_definitions.yaml`

## 10. Simple Linear Prior

Answered by: `results/full_repro/baseline_comparator_table.csv`

## 11. Axis Dominance

Answered by: `results/full_repro/single_axis_dominance_table.csv`

## 12. Split Uncertainty

Answered by: `results/full_repro/split_uncertainty_table.csv`

## 13. Model Heterogeneity

Answered by: `results/full_repro/per_model_results.csv`

## 14. q=4 Scaling Analog

Answered by: `results/full_repro/budget_curve.csv`
