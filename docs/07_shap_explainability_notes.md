# SHAP Explainability Notes — Phase 3

## What we built
Per-transaction explanations using shap.TreeExplainer on the trained
XGBoost model, showing which features drove each individual prediction
up or down, not just a global feature importance ranking.

## Initial finding: saturated explanations on extreme-amount transactions
The top-5-by-score transactions all had nearly identical SHAP
explanations despite differing in amount by over $150,000. This reflects
a real property of tree-based models: with max_depth=5 and few training
examples above a certain amount threshold, the model has no learned
splits to further differentiate within that extreme range -- all such
transactions route to the same terminal leaf. Not a bug; a genuine
model characteristic worth understanding.

## Varied example analysis (high-confidence TP + 2 false positives)
Both false positives examined were CASH_OUT transactions where
balance_mismatch was the dominant contributor to an incorrectly high
score. The one high-confidence true positive (a fraudulent TRANSFER)
was also driven primarily by type_TRANSFER and balance_mismatch.

## Key insight
balance_mismatch is genuinely predictive of fraud (it appears as a top
driver in the true positive), but it is also a leading driver of false
positives -- suggesting it is a noisy signal: real, non-fraudulent
transactions can also show balance inconsistencies (e.g. rounding,
fees, partial holds), which the current binary (mismatch / no mismatch)
formulation cannot distinguish from fraud-driven inconsistencies.

## Future improvement (documented, not implemented in this pass)
Refining balance_mismatch from a binary flag into a continuous magnitude
(how large is the mismatch, not just whether one exists) could plausibly
reduce false positives while preserving true-positive detection. Not
implemented here to keep this phase's scope honest and bounded, but
recorded as a concrete, evidence-based next step.
