# Null Recompute Report

Null name: prevalence_preserving_within_surface_label_shuffle
Shuffle unit: eligible nonconstant AFC model-scenario surface
Preserves: surface ID and positive/negative label counts
Destroys: coordinate-to-label assignment within each surface
Split semantics: 100 q=12 balanced-random split masks per surface using the original stable-seed rule
Aggregation: mean of model-level mean hidden balanced accuracy

Replicates: 5000
Eligible surfaces: 77
Models: 10
Observed BA: 0.746930020075565
Null mean: 0.522558570262308
Null SD: 0.005160473005287
Null exceedances >= observed: 0 / 5000
Runtime seconds: 5.586
- claude-haiku-4-5: 5 surfaces
- claude-opus-4-6: 12 surfaces
- deepseek-r1: 11 surfaces
- gemini-2.5-pro: 6 surfaces
- gemini-3-flash-preview: 7 surfaces
- gpt-5-mini: 5 surfaces
- gpt-5.2: 7 surfaces
- gpt-5.4-thinking: 9 surfaces
- gpt-health: 10 surfaces
- llama-3.3-70b-instruct-turbo: 5 surfaces