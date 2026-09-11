# Ensemble Scoring Notes — Phase 3

## Design
ensemble_score = 0.9 * model_score + 0.1 * anomaly_score (normalized 0-1)
Weights were chosen deliberately based on measured component performance
(see docs/05_anomaly_detection_notes.md), not equal-by-default weighting.
fan-in was excluded entirely, since it was shown to reflect legitimate
agent activity rather than fraud (docs/06_graph_intelligence_notes.md).

## Honest result: comparing model-only vs ensemble
Using the model-only-calibrated threshold (0.8485) directly on ensemble
scores gave misleading numbers (precision appeared to jump from 0.17 to
0.44) because the ensemble's score range is compressed relative to the
model-only range -- applying the same raw threshold to a differently-
scaled distribution is not a fair comparison.

The threshold-independent metric (PR-AUC) is the fair comparison:
- Model only: PR-AUC = 0.7971
- Ensemble:   PR-AUC = 0.7841

Conclusion: on this labeled test set, the ensemble does NOT outperform
the supervised model alone. This is expected and consistent with the
anomaly detector's near-zero measured overlap with known fraud -- adding
its signal introduces mild noise rather than genuine improvement,
against fraud we can actually measure.

## Why the anomaly detector is retained anyway
Its value proposition is catching fraud patterns not present in current
labeled data -- by construction, this cannot be measured against a test
set built from the same labeling process. Retaining it is a deliberate
architectural choice for future/unknown fraud coverage, not a metric-
driven one. This tradeoff (accepting no measured benefit now, for
theoretical future coverage) is stated honestly rather than implied to
already show up as an improvement in current numbers.

## What would change this
The ensemble weighting could be revisited once real production feedback
exists (investigator-confirmed fraud not caught by the supervised model)
that traces back to something the anomaly detector did catch. Until
such evidence exists, the 0.9/0.1 weighting is a conservative, honestly-
labeled placeholder, not a tuned result.
