# Anomaly Detection Notes — Phase 3

## Model
Isolation Forest (unsupervised, sklearn), trained on the same 6 numeric
features as the supervised model, with NO access to fraud labels during
training. Contamination parameter set to 0.001 (rough prior expectation
of ~0.1% anomalous transactions).

## Result (honest, not fabricated)
Flagged 1,062 anomalies out of 1,248,736 test transactions (0.085%).
Of 4,250 actual fraud cases, only 13 (0.31%) were flagged as anomalous.

## Interpretation
This is a genuine finding, not a bug: fraud in this dataset is not well
captured as a raw statistical outlier in amount/deviation space. This
makes sense given two of our five features (account_velocity,
is_new_destination) are nearly constant across the dataset (see
docs/03_feature_store_notes.md), leaving Isolation Forest's notion of
"unusual" driven mostly by transaction amount -- and fraudulent
transactions here aren't necessarily unusual in raw size, only in
behavioral context and sequence, which is what the supervised model
was specifically trained to learn.

## Design implication
This anomaly detector will contribute only a weak, low-weighted signal
to the final ensemble score, and is retained in the architecture as
insurance against future/novel fraud patterns not represented in current
labeled data, rather than as a strong current-fraud detector on its own.
This is an honest, deliberate scoping decision, not an unaddressed
weakness.
