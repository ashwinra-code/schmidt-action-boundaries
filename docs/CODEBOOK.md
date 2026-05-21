# Codebook

This codebook defines the main generated tables used by the retrospective AFC proof-of-concept package.

## `results/full_repro/afc_cell_table_from_raw.csv`

One row per rebuilt model-scenario-cell AFC observation.

Key fields:

- `model_name`, `model_snapshot`: model identity.
- `scenario_id`, `surface_id`: scenario and response-surface identifiers.
- `cell_id`: 5-axis Boolean cell coordinate encoded as an integer.
- `axis_anchor`, `axis_access`, `axis_black`, `axis_woman`, `axis_objective`: reconstructed design axes.
- `acceptable_floor_choice`: primary AFC endpoint label.
- `source_response_id`: provenance pointer to the parsed response.

## `results/full_repro/surface_assembly_table.csv`

One row per AFC model-scenario group.

Key fields:

- `n_cells_observed`, `n_unique_cell_ids`: surface completeness checks.
- `is_complete_32_cell_surface`: whether all 32 cells are present.
- `is_constant_afc`: whether the primary endpoint has no boundary.
- `eligibility_status`: inclusion status for boundary-recovery analysis.

## `data/splits/full_repro/q12_split_manifest.csv`

Locked q=12 split-mask manifest replayed by the strict runner.

Key fields:

- `split_id`, `surface_id`, `model_name`, `scenario_id`: split identity.
- `observed_cell_ids`, `hidden_cell_ids`: observed and scored cells.
- `q`: observed-cell budget.
- `mask_generation_rule`, `used_outcome_labels`, `used_full_surface_labels`: leakage-audit fields.

## `results/full_repro/hidden_predictions.csv`

One row per hidden-cell prediction.

Key fields:

- `surface_id`, `split_id`, `cell_id`: scored hidden cell.
- `true_label`, `predicted_label`, `predicted_score`: scoring inputs and output.
- `model_name`, `scenario_id`: grouping fields for aggregation.

## `results/full_repro/split_level_metrics.csv`

One row per surface split after hidden-cell scoring.

Key fields:

- `hidden_balanced_accuracy`: primary split-level BA.
- `majority_balanced_accuracy`: majority baseline under the implemented metric rule.
- `lift`: primary BA minus majority baseline.
- one-class hidden-set indicators used by the metric anomaly replay.

## `results/full_repro/main_result_table.csv`

Final headline metric table.

Expected values:

- Mean hidden BA: `0.74693002007556464`
- Majority baseline: `0.52508604978354989`
- Mean lift: `0.22184397029201483`
- Models with positive lift: `10 / 10`

## `results/full_repro/null_distribution_raw_recomputed.csv`

One row per prevalence-preserving within-surface label-shuffle replicate recomputed from raw-built labels.

Key fields:

- `replicate_id`: null replicate number.
- `null_mean_hidden_balanced_accuracy`: aggregate null BA.
- `exceeds_observed`: whether the replicate met or exceeded the observed BA.

## `results/full_repro/null_permutation_manifest.csv`

Permutation audit manifest for the null recomputation.

Key fields:

- `replicate_id`, `surface_id`, `seed`: deterministic randomization identifiers.
- `permutation_hash`: compact audit hash of the label permutation.
- `n_positive_preserved`, `n_negative_preserved`: prevalence-preservation checks.

## `results/full_repro/denominator_table.csv`

Layer-by-layer denominator flow.

Expected strict denominator:

- `150` AFC model-scenario groups
- `4` incomplete groups preserved separately
- `146` complete 32-cell surfaces
- `77` nonconstant eligible surfaces

## `results/full_repro/budget_curve.csv` and `results/full_repro/hamming_depth_table.csv`

Secondary robustness artifacts. These are included for reviewer context and are labeled in reports as generated or replayed according to their script-specific provenance.
