# Model Training Notes — Phase 3

## Model
XGBoost classifier, trained on 5,113,884 rows (chronological first 80% of
the simulation), evaluated on 1,248,736 held-out rows (chronological last
20% -- a genuinely harder test set due to a 4.4x higher fraud rate than
train, see docs/03_feature_store_notes.md for the concept drift finding).

## Features used
account_velocity, amount_deviation, balance_mismatch, is_new_destination,
dest_velocity, amount, one-hot encoded transaction type.

## Class imbalance handling
scale_pos_weight = 1289.4 (ratio of legitimate to fraud transactions in
training data), passed directly to XGBoost rather than resampling the
data -- keeps the full, honest data distribution intact during training.

## Default threshold (0.5) results
Precision: 0.0873 | Recall: 0.9814 | F1: 0.1603 | PR-AUC: 0.7971

At the default threshold the model catches 98% of fraud but at the cost of
roughly 10 false alarms for every true catch. This is a direct, expected
consequence of the recall-heavy class weighting, not a flaw in the model.

## Threshold trade-off analysis
| Recall | Precision |
|--------|-----------|
| 49.9%  | 96.9%     |
| 70.1%  | 82.4%     |
| 80.0%  | 55.8%     |
| 90.0%  | 17.3%     |
| 95.0%  | 10.9%     |

## Chosen operating point: ~80% recall / ~56% precision
Rationale: below this point, too much real fraud is missed for a fraud
system to be useful. Above this point, precision degrades so fast that
investigators would face unsustainable false-alarm rates ("alert
fatigue"), a well-known real-world failure mode in fraud operations.
80/56 represents a deliberate, defensible business trade-off between
missed fraud and investigator workload, not an arbitrary default.

## PR-AUC as the threshold-independent metric
PR-AUC of 0.7971 (vs. a random-baseline PR-AUC equal to the fraud rate,
~0.003) confirms the model has learned genuine, strong ranking signal,
independent of any specific threshold choice.

## Precision/recall are a fundamental trade-off, not a solvable gap
There is no threshold that maximizes both simultaneously on imbalanced
fraud data -- this mirrors every real detection system (spam filters,
medical screening, smoke detectors). The defensible answer in an
interview is not a specific number, but the demonstrated ability to
measure the trade-off honestly and choose a deliberate operating point.
