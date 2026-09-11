# Feature Store Notes — Phase 2 (Feast)

## Why a feature store, specifically
Without it, feature logic used at training time and feature logic used at
serving time can silently drift apart -- different rounding, different time
windows, a forgotten edge case. This is a well-known ML engineering problem
called training-serving skew, and it is one of the most common causes of a
model performing well in testing but poorly in production.

Feast solves this by having both training and live serving pull from the
same registered feature definitions, instead of two independently
maintained code paths.

## Architecture
- Offline store: Postgres (source of truth for historical data, used later
  for training)
- Online store: Redis (fast key-value lookups at inference time)
- Push source: our Kafka consumer computes features per transaction and
  pushes them to Feast in real time via store.push(), rather than writing
  to Redis directly

## Verified end-to-end
1. Consumer reads a transaction from Kafka
2. Computes account_velocity, amount_deviation, balance_mismatch,
   is_new_destination using Redis-backed running state
3. Pushes the computed row to Feast via transactions_push_source
4. Independently confirmed by reading the same account back out through
   store.get_online_features() -- values matched exactly what was pushed

## Design note
Redis is used in two related but distinct ways here: directly, by our
consumer, for cheap running counters (sums, counts, sets) that don't need
Feast's schema; and indirectly, as Feast's online store backend, for the
final computed feature values Feast serves. Worth being able to explain
this distinction clearly, since it can look redundant at first glance.
