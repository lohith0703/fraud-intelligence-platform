import pandas as pd

DATA_PATH = "data/raw/PS_20174392719_1491204439457_log.csv"

print("Loading dataset...")
df = pd.read_csv(DATA_PATH)

print("\n--- Shape ---")
print(f"Rows: {df.shape[0]:,}")
print(f"Columns: {df.shape[1]}")

print("\n--- Columns & dtypes ---")
print(df.dtypes)

print("\n--- Transaction types ---")
print(df["type"].value_counts())

print("\n--- Fraud label distribution ---")
fraud_counts = df["isFraud"].value_counts()
print(fraud_counts)
fraud_rate = df["isFraud"].mean() * 100
print(f"\nFraud rate: {fraud_rate:.4f}%")

print("\n--- isFlaggedFraud distribution (simulator's own naive rule) ---")
print(df["isFlaggedFraud"].value_counts())

print("\n--- Fraud rate by transaction type ---")
print(df.groupby("type")["isFraud"].mean() * 100)

print("\n--- Sample rows ---")
print(df.head(3))