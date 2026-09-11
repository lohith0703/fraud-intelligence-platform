import psycopg2
from psycopg2.extras import execute_values

CHUNK_SIZE = 100_000

conn = psycopg2.connect(
    host="localhost", port=5433, dbname="fraud_db",
    user="fraud_user", password="fraud_pass"
)
read_cur = conn.cursor(name="feature_scan_cursor", withhold=True)  # server-side cursor: avoids loading 6.3M rows into memory at once; withhold=True lets it survive commits
write_cur = conn.cursor()

read_cur.execute("""
    SELECT transaction_id, step, type, amount, orig_account_id, dest_account_id,
           oldbalance_orig, newbalance_orig, created_at
    FROM transactions
    ORDER BY step, transaction_id
""")

# Per-account running state, kept in memory for this single pass
velocity = {}
amount_sum = {}
amount_count = {}
dest_seen = {}

buffer = []
processed = 0

def flush():
    if buffer:
        execute_values(write_cur, """
            INSERT INTO transaction_features
                (transaction_id, orig_account_id, event_timestamp,
                 account_velocity, amount_deviation, balance_mismatch, is_new_destination)
            VALUES %s
        """, buffer)
        conn.commit()
        buffer.clear()

while True:
    rows = read_cur.fetchmany(CHUNK_SIZE)
    if not rows:
        break

    for (txn_id, step, ttype, amount, orig, dest,
         oldbal, newbal, created_at) in rows:

        # Feature 1: velocity
        velocity[orig] = velocity.get(orig, 0) + 1
        v = velocity[orig]

        # Feature 2: amount deviation from running average
        amount_sum[orig] = amount_sum.get(orig, 0.0) + float(amount)
        amount_count[orig] = amount_count.get(orig, 0) + 1
        avg = amount_sum[orig] / amount_count[orig]
        deviation = round(float(amount) - avg, 2)

        # Feature 3: balance consistency (direction depends on type)
        if ttype == "CASH_IN":
            expected = float(oldbal) + float(amount)
        else:
            expected = float(oldbal) - float(amount)
        mismatch = abs(expected - float(newbal)) > 0.01

        # Feature 4: destination novelty
        seen = dest_seen.setdefault(orig, set())
        is_new_dest = dest not in seen
        seen.add(dest)

        buffer.append((txn_id, orig, created_at, v, deviation, mismatch, is_new_dest))

    flush()
    processed += len(rows)
    print(f"Processed {processed:,} rows...")

read_cur.close()
write_cur.close()
conn.close()
print("Done computing batch features.")