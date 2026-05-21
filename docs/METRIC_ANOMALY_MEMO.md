# Metric Anomaly Memo

The majority baseline in the reported result is `0.525086`, not the theoretical binary constant-class balanced accuracy of `0.500`.

Reason: the implemented majority baseline is trained on the observed q cells for each split, then thresholded at `0.5` and scored on hidden cells. Hidden balanced accuracy averages the class recalls that are defined in the hidden set. If a hidden split contains only one class, the metric averages only that class recall rather than forcing an undefined class recall into the denominator.

For the primary q=12 `balanced_random` split manifest:

- Split rows: 77,000
- One-class hidden splits: 4,081
- One-class hidden split fraction: 0.053
- Implemented majority baseline: 0.525086

Interpretation: `0.525086` is an implementation-specific, query-trained baseline under the released split masks. It should not be described as the theoretical balanced-accuracy baseline for a constant binary classifier.
