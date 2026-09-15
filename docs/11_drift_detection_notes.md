# Drift Detection Notes — Phase 4

## Method
Population Stability Index (PSI), comparing train (reference) vs test
(current) distributions for amount, amount_deviation, dest_velocity, and
is_fraud directly.

## Finding 1: Feature-level PSI missed known concept drift
amount, amount_deviation, and dest_velocity all showed PSI < 0.002 (no
significant shift), despite Phase 3 already establishing a real,
independently-verified 4.39x fraud rate shift between these same two
windows. This demonstrates PSI's real limitation: it measures shifts in
a feature's own distribution, not shifts in the relationship between
features and the label (concept drift). A feature can look perfectly
stable while what it predicts has changed completely.

## Bug found and fixed: percentile binning fails on skewed binary variables
Initial attempt to compute PSI directly on is_fraud using the same
percentile-bucketing method as continuous features returned PSI = 0.0,
which was wrong. Root cause: percentile-based bucketing collapses when
applied to an extremely skewed 0/1 variable (over 99.9% zeros), since
most percentile cutpoints land on the same value. Fixed by computing
PSI directly on the two explicit categories (fraud/not fraud) rather
than percentile bins.

## Finding 2: standard PSI thresholds fail on rare-event labels
After the fix, PSI on is_fraud came out to 0.0039 -- still classified as
"no significant shift" under standard thresholds (0.1 = moderate, 0.25 =
significant), despite reflecting a real, independently-verified 4.39x
fraud rate change. Root cause: PSI's standard thresholds were calibrated
for moderately-distributed variables; on an extremely low base-rate
variable like fraud, even a large *relative* shift produces a small
*absolute* PSI value, because PSI fundamentally measures absolute
proportion differences.

## Practical conclusion
Standard PSI monitoring, using standard thresholds, is not sufficient on
its own to catch fraud-rate drift in a system like this. A real
production system would need to monitor the raw fraud/flagging rate
directly, with thresholds calibrated specifically for its own rare-event
base rate, rather than relying on PSI's default, off-the-shelf
interpretation bands. This is a genuine, evidence-based limitation
discovered through testing, not a theoretical caveat.
