import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

DATA_PATH = "data/raw/PS_20174392719_1491204439457_log.csv"
CHUNK_SIZE = 100_000

conn = psycopg2.connect(
    host="localhost", port=5433, dbname="fraud_db",
    user="fraud_user", password="fraud_pass"
)
cur = conn.cursor()

seen_accounts = set()

def account_type(acct_id):
    return "merchant" if acct_id.startswith("M") else "customer"

row_offset = 0
for chunk in pd.read_csv(DATA_PATH, chunksize=CHUNK_SIZE):
    # 1. Insert any new accounts seen in this chunk
    accounts_in_chunk = set(chunk["nameOrig"]).union(set(chunk["nameDest"]))
    new_accounts = accounts_in_chunk - seen_accounts
    if new_accounts:
        account_rows = [(a, account_type(a)) for a in new_accounts]
        execute_values(
            cur,
            "INSERT INTO accounts (account_id, account_type) VALUES %s ON CONFLICT DO NOTHING",
            account_rows,
        )
        seen_accounts.update(new_accounts)

    # 2. Insert transactions, assigning our own sequential IDs so we can link fraud_labels
    chunk = chunk.reset_index(drop=True)
    chunk["transaction_id"] = chunk.index + row_offset + 1

    txn_rows = list(chunk[[
        "transaction_id", "step", "type", "amount", "nameOrig", "nameDest",
        "oldbalanceOrg", "newbalanceOrig", "oldbalanceDest", "newbalanceDest"
    ]].itertuples(index=False, name=None))

    execute_values(cur, """
        INSERT INTO transactions
            (transaction_id, step, type, amount, orig_account_id, dest_account_id,
             oldbalance_orig, newbalance_orig, oldbalance_dest, newbalance_dest)
        VALUES %s
    """, txn_rows)

    # 3. Insert fraud labels for this chunk
    label_rows = [
        (tid, bool(f), bool(ff))
        for tid, f, ff in chunk[["transaction_id", "isFraud", "isFlaggedFraud"]].itertuples(index=False, name=None)
    ]
    execute_values(
        cur,
        "INSERT INTO fraud_labels (transaction_id, is_fraud, is_flagged_fraud) VALUES %s",
        label_rows,
    )

    conn.commit()
    row_offset += len(chunk)
    print(f"Loaded {row_offset:,} rows...")

cur.close()
conn.close()
print("Done.")