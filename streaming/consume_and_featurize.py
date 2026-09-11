import json
import pandas as pd
from datetime import datetime, timezone
from kafka import KafkaConsumer
import redis
from feast import FeatureStore

r = redis.Redis(host="localhost", port=6379, decode_responses=True)
store = FeatureStore(repo_path="feature_store/fraud_features/feature_repo")

consumer = KafkaConsumer(
    "transactions",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    group_id="feature-engineering-consumer",
)

print("Listening for transactions, computing features, and pushing to Feast...\n")

for message in consumer:
    txn = message.value
    account = txn["orig_account_id"]

    # --- Feature 1: transaction velocity (sender side) ---
    velocity_key = f"velocity:{account}"
    txn_count = r.incr(velocity_key)

    # --- Feature 5: destination velocity ---
    dest_velocity_key = f"dest_velocity:{txn['dest_account_id']}"
    dest_velocity = r.incr(dest_velocity_key)

    # --- Feature 2: running average amount ---
    sum_key = f"amount_sum:{account}"
    count_key = f"amount_count:{account}"
    r.incrbyfloat(sum_key, txn["amount"])
    prev_count = r.incr(count_key)
    total_amount = float(r.get(sum_key))
    avg_amount = total_amount / prev_count
    amount_deviation = txn["amount"] - avg_amount

    # --- Feature 3: balance consistency check ---
    if txn["type"] == "CASH_IN":
        expected_new_balance = txn["oldbalance_orig"] + txn["amount"]
    else:
        expected_new_balance = txn["oldbalance_orig"] - txn["amount"]
    balance_mismatch = abs(expected_new_balance - txn["newbalance_orig"]) > 0.01

    # --- Feature 4: destination novelty ---
    dest_seen_key = f"dest_seen:{account}"
    is_new_destination = not r.sismember(dest_seen_key, txn["dest_account_id"])
    r.sadd(dest_seen_key, txn["dest_account_id"])

    # --- Push to Feast ---
    df = pd.DataFrame([{
        "orig_account_id": account,
        "event_timestamp": datetime.now(timezone.utc),
        "account_velocity": int(txn_count),
        "amount_deviation": float(round(amount_deviation, 2)),
        "balance_mismatch": bool(balance_mismatch),
        "is_new_destination": bool(is_new_destination),
        "dest_velocity": int(dest_velocity),
    }])
    store.push("transactions_push_source", df)

    print(f"txn={txn['transaction_id']} account={account} "
          f"velocity={txn_count} dest_vel={dest_velocity} "
          f"amt_dev={round(amount_deviation, 2)} "
          f"bal_mismatch={balance_mismatch} new_dest={is_new_destination} "
          f"fraud={txn['is_fraud']} -> pushed to Feast")