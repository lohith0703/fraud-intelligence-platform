import json
import time
import psycopg2
from kafka import KafkaProducer

conn = psycopg2.connect(
    host="localhost", port=5433, dbname="fraud_db",
    user="fraud_user", password="fraud_pass"
)
cur = conn.cursor()

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# Pull a manageable slice for our first test run: first 500 transactions by step order
cur.execute("""
    SELECT t.transaction_id, t.step, t.type, t.amount,
           t.orig_account_id, t.dest_account_id,
           t.oldbalance_orig, t.newbalance_orig,
           t.oldbalance_dest, t.newbalance_dest,
           f.is_fraud
    FROM transactions t
    JOIN fraud_labels f ON t.transaction_id = f.transaction_id
    ORDER BY t.step, t.transaction_id
    LIMIT 500;
""")

rows = cur.fetchall()
columns = ["transaction_id", "step", "type", "amount", "orig_account_id",
           "dest_account_id", "oldbalance_orig", "newbalance_orig",
           "oldbalance_dest", "newbalance_dest", "is_fraud"]

print(f"Streaming {len(rows)} transactions to Kafka topic 'transactions'...")

for row in rows:
    event = dict(zip(columns, row))
    event["amount"] = float(event["amount"])
    event["oldbalance_orig"] = float(event["oldbalance_orig"])
    event["newbalance_orig"] = float(event["newbalance_orig"])
    event["oldbalance_dest"] = float(event["oldbalance_dest"])
    event["newbalance_dest"] = float(event["newbalance_dest"])

    producer.send("transactions", value=event)
    print(f"Sent transaction_id={event['transaction_id']} "
          f"type={event['type']} amount={event['amount']} fraud={event['is_fraud']}")
    time.sleep(0.05)  # small delay so it visibly streams instead of instantly dumping

producer.flush()
cur.close()
conn.close()
print("Done streaming.")