# Feature Engineering Notes — Phase 2

## Features implemented (v1)
- account_velocity: running transaction count per account (Redis INCR)
- amount_deviation: transaction amount vs account's running average
- balance_mismatch: derived consistency check (not raw balance columns)
- is_new_destination: whether this account has sent to this destination before

## Bug found and fixed: balance_mismatch direction
Initial implementation assumed oldbalance - amount = newbalance for all
transaction types. This is correct for money leaving an account (PAYMENT,
TRANSFER, CASH_OUT, DEBIT), but wrong for CASH_IN, where money enters the
account (oldbalance + amount = newbalance).

Caught by observing false balance_mismatch=True flags on legitimate CASH_IN
transactions during manual testing. Fixed by branching the check on
transaction type.

Lesson: transaction-type-dependent logic needs explicit handling, not a
single formula assumed to generalize across all types.

## State backend: Redis
Chosen over in-memory Python dict because state must survive consumer
restarts -- an in-memory dict resets to zero on every restart, which would
make velocity tracking silently wrong after any deploy or crash. Verified
by restarting the consumer between two producer runs and confirming
velocity counts continued incrementing rather than resetting.
