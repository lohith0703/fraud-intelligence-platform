import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

print("Loading training data...")
train_df = pd.read_parquet("data/train.parquet")
test_df = pd.read_parquet("data/test.parquet")

feature_cols = [
    "account_velocity", "amount_deviation", "balance_mismatch",
    "is_new_destination", "dest_velocity", "amount"
]

X_train = train_df[feature_cols].astype(float)
X_test = test_df[feature_cols].astype(float)
y_test = test_df["is_fraud"].astype(int)

# Isolation Forest is unsupervised -- it never sees y_train / is_fraud during training
print("Training Isolation Forest (unsupervised, no labels used)...")
iso_forest = IsolationForest(
    n_estimators=200,
    contamination=0.001,  # rough prior: we expect ~0.1% of transactions to be anomalous
    random_state=42,
    n_jobs=-1,
)
iso_forest.fit(X_train)

# decision_function: higher = more normal, lower = more anomalous
# We flip the sign so higher = more anomalous, matching intuition
anomaly_scores = -iso_forest.decision_function(X_test)
predictions = iso_forest.predict(X_test)  # -1 = anomaly, 1 = normal
is_anomaly = (predictions == -1)

print(f"\nFlagged {is_anomaly.sum():,} anomalies out of {len(X_test):,} test transactions "
      f"({is_anomaly.mean()*100:.4f}%)")

# Cross-check against actual fraud labels (informational only -- this model never saw labels)
caught_fraud = ((is_anomaly) & (y_test == 1)).sum()
total_fraud = (y_test == 1).sum()
print(f"Of {total_fraud} actual fraud cases, anomaly detector flagged {caught_fraud} "
      f"({caught_fraud / total_fraud * 100:.2f}%) as anomalous -- WITHOUT ever seeing labels")

joblib.dump(iso_forest, "ml/anomaly_detector.joblib")
print("\nModel saved to ml/anomaly_detector.joblib")