import json
from datetime import datetime
from kafka import KafkaConsumer
import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

consumer = KafkaConsumer(
    "transactions",
    bootstrap_servers="localhost:9092",
    auto_offset_reset="earliest",
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    group_id="feature-engineering-consumer",
)

print("Listening for transactions and computing features...\n")

for message in consumer:
    txn = message.value
    account = txn["orig_account_id"]

    # --- Feature 1: transaction velocity (count in Redis, no expiry yet — simple version) ---
    velocity_key = f"velocity:{account}"
    txn_count = r.incr(velocity_key)

    # --- Feature 2: running average amount for this account ---
    sum_key = f"amount_sum:{account}"
    count_key = f"amount_count:{account}"
    r.incrbyfloat(sum_key, txn["amount"])
    prev_count = r.incr(count_key)
    total_amount = float(r.get(sum_key))
    avg_amount = total_amount / prev_count
    amount_deviation = txn["amount"] - avg_amount

 # --- Feature 3: balance consistency check (direction depends on transaction type) ---
    if txn["type"] == "CASH_IN":
        expected_new_balance = txn["oldbalance_orig"] + txn["amount"]
    else:
        expected_new_balance = txn["oldbalance_orig"] - txn["amount"]
    balance_mismatch = abs(expected_new_balance - txn["newbalance_orig"]) > 0.01

    # --- Feature 4: destination novelty ---
    dest_seen_key = f"dest_seen:{account}"
    is_new_destination = not r.sismember(dest_seen_key, txn["dest_account_id"])
    r.sadd(dest_seen_key, txn["dest_account_id"])

    features = {
        "transaction_id": txn["transaction_id"],
        "account_velocity": txn_count,
        "amount_deviation": round(amount_deviation, 2),
        "balance_mismatch": balance_mismatch,
        "is_new_destination": is_new_destination,
        "is_fraud": txn["is_fraud"],
    }

    print(f"txn={features['transaction_id']} "
          f"velocity={features['account_velocity']} "
          f"amt_dev={features['amount_deviation']} "
          f"bal_mismatch={features['balance_mismatch']} "
          f"new_dest={features['is_new_destination']} "
          f"fraud={features['is_fraud']}")