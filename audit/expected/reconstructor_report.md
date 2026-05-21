# Reconstructor Report

Model family: degree-1 ridge regression
Features: intercept plus five main effects
Axis encoding: 0/1 cell axes transformed to -1/+1
Regularization: ridge lambda=1.0; intercept penalty=1e-9
Threshold: predicted score >= 0.5
Solver: package-local Gauss-Jordan solver over the 6 x 6 ridge normal equations
One-class observed-split handling: constant score equal to observed class
One-class hidden-split handling: balanced accuracy averages only defined class recall
Aggregation hierarchy: hidden cell -> split metric -> model mean -> cross-model mean

Hidden prediction rows: 1540000
Split metrics: 77000
Mean hidden BA: 0.74693002007556464
Majority baseline: 0.52508604978354989
Mean lift: 0.22184397029201483