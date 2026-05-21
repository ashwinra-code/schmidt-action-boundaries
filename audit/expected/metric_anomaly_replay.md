# Metric Anomaly Replay

Number of hidden splits with both classes: 72919
Number of hidden splits with only positives: 3105
Number of hidden splits with only negatives: 976

Balanced accuracy rule:
- Hidden set has both classes: average positive and negative recall.
- Hidden set has only positives: use positive recall only.
- Hidden set has only negatives: use negative recall only.

Majority baseline under implemented primary aggregation: 0.525086049784
Majority baseline under split-pooled aggregation: 0.526422077922
Theoretical binary constant baseline when both classes are present: 0.500000
Majority baseline after excluding one-class hidden splits: 0.500000000000
Degree-1 BA after excluding one-class hidden splits: 0.735497599494
Degree-1 lift after excluding one-class hidden splits: 0.235497599494

The implemented majority baseline is above 0.500 because split-level balanced accuracy is averaged after applying the available-class rule to one-class hidden splits.