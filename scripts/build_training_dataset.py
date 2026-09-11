import pandas as pd
import psycopg2

conn = psycopg2.connect(
    host="localhost", port=5433, dbname="fraud_db",
    user="fraud_user", password="fraud_pass"
)

query = """
    SELECT
        tf.transaction_id,
        t.step,
        t.type,
        t.amount,
        tf.account_velocity,
        tf.amount_deviation,
        tf.balance_mismatch,
        tf.is_new_destination,
        tf.dest_velocity,
        f.is_fraud
    FROM transaction_features tf
    JOIN transactions t ON tf.transaction_id = t.transaction_id
    JOIN fraud_labels f ON tf.transaction_id = f.transaction_id
    ORDER BY t.step, tf.transaction_id
"""

print("Loading joined dataset from Postgres...")
df = pd.read_csv  # placeholder removed below
df = pd.read_sql(query, conn)
conn.close()

print(f"Total rows: {len(df):,}")

# Time-based split: first 80% of steps = train, last 20% = test
cutoff_step = df["step"].quantile(0.8)
train_df = df[df["step"] <= cutoff_step].copy()
test_df = df[df["step"] > cutoff_step].copy()

print(f"Cutoff step: {cutoff_step}")
print(f"Train rows: {len(train_df):,} | fraud in train: {train_df['is_fraud'].sum():,} ({train_df['is_fraud'].mean()*100:.4f}%)")
print(f"Test rows:  {len(test_df):,} | fraud in test:  {test_df['is_fraud'].sum():,} ({test_df['is_fraud'].mean()*100:.4f}%)")

train_df.to_parquet("data/train.parquet", index=False)
test_df.to_parquet("data/test.parquet", index=False)
print("Saved data/train.parquet and data/test.parquet")