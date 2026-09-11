# Graph Intelligence Notes — Phase 3

## Investigation 1: Fan-in (mule account) detection
Hypothesis: destination accounts receiving from many distinct senders,
which then quickly send money onward, indicate money-mule behavior.

Finding: 280,200 accounts received from 5+ distinct senders (146,629 from
10+, max 113). Manually inspecting the highest fan-in accounts showed
every one sent exactly 1 outgoing transaction regardless of how many
senders it received from -- but on inspection, the outgoing transaction
amounts did not match the sum of incoming funds, and the transactions
were not labeled fraud.

Conclusion: high fan-in in this dataset corresponds to CASH_IN/CASH_OUT
agent accounts (legitimate intermediaries that naturally interact with
many different customers), not money-mule behavior. This is expected,
legitimate business activity, not a fraud signal on its own.

## Investigation 2: TRANSFER -> CASH_OUT chain detection
Hypothesis: PaySim's fraud mechanism involves an account receiving a
fraudulent TRANSFER, then cashing it out via a CASH_OUT from that same
account (a classic layering pattern).

Tested by joining fraudulent TRANSFER destination accounts against
CASH_OUT transactions originating from those same accounts, with no
timing/amount constraints. Result: only 3 matches out of thousands of
fraudulent transfers, and none had matching fraud status or amount on
both sides.

Conclusion: this chain pattern is structurally almost absent from the
data. Root cause: 99.85% of accounts in this dataset transact exactly
once, ever (established in docs/03_feature_store_notes.md). A two-hop
chain requires an account to transact twice -- which is already rare
across the whole dataset, fraud or not. This is not a detection failure;
it's a structural property of how PaySim generates its transaction
graph.

## Broader dataset limitation (honest, not worked around)
PaySim contains no device ID, IP address, or other shared-identifier
fields. Classic graph-based fraud signals (shared device/IP across
seemingly unrelated accounts, coordinated account rings) are not
representable in this dataset at all -- this is a limitation of the data
source, not of the modeling approach.

## Scope decision
Graph-based fraud intelligence for this project is scoped down to:
- Fan-in count (distinct senders per destination) as a weak, minor
  feature contribution to the final ensemble, explicitly documented as
  reflecting legitimate agent activity more than fraud
- A visualized example of the actual account-transaction graph structure
  for the dashboard's Graph Intelligence page, for illustrative/portfolio
  purposes

Full multi-hop money-laundering chain detection and device/IP-based ring
detection are documented as future improvements requiring a richer
dataset (device/IP fields, longer observation windows with more repeat
account activity) -- not attempted here, and explicitly not claimed as
working.

## Why this is a legitimate outcome, not a failure
Testing a specific, evidence-based hypothesis (informed by the actual
fraud examples seen in Phase 1) and honestly reporting that the data
doesn't support it -- with a clear structural explanation -- is stronger
engineering practice than fabricating a chain-detection feature that
doesn't actually reflect anything real in the underlying data.
