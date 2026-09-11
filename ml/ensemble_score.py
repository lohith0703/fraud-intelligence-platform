import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
from sklearn.metrics import precision_score, recall_score, average_precision_score

print("Loading model, anomaly detector, and test data...")
model = xgb.XGBClassifier()
model.load_model("ml/fraud_model.json")
iso_forest = joblib.load("ml/anomaly_detector.joblib")

test_df = pd.read_parquet("data/test.parquet")

feature_cols_numeric = [
    "account_velocity", "amount_deviation", "balance_mismatch",
    "is_new_destination", "dest_velocity", "amount"
]
test_encoded = pd.get_dummies(test_df, columns=["type"], prefix="type")
type_cols = [c for c in test_encoded.columns if c.startswith("type_")]
feature_cols = feature_cols_numeric + type_cols

X_test_model = test_encoded[feature_cols].astype(float)
X_test_anomaly = test_df[feature_cols_numeric].astype(float)
y_test = test_df["is_fraud"].astype(int)

# Component 1: supervised model probability (0-1, already well-calibrated in range)
model_scores = model.predict_proba(X_test_model)[:, 1]

# Component 2: anomaly score, normalized to 0-1 range to combine fairly with model_scores
raw_anomaly = -iso_forest.decision_function(X_test_anomaly)
anomaly_scores = (raw_anomaly - raw_anomaly.min()) / (raw_anomaly.max() - raw_anomaly.min())

# Deliberate, low weight on anomaly detector -- reflects its measured near-zero overlap
# with known fraud (see docs/05_anomaly_detection_notes.md). Included as insurance against
# novel fraud patterns not present in current labels, not as a performance booster.
MODEL_WEIGHT = 0.9
ANOMALY_WEIGHT = 0.1

ensemble_scores = MODEL_WEIGHT * model_scores + ANOMALY_WEIGHT * anomaly_scores

# Compare: does the ensemble help, hurt, or barely change things vs. the model alone?
# Using our previously chosen operating threshold's approximate score cutoff for fair comparison
THRESHOLD = 0.8485  # the threshold we chose for ~80% recall / ~56% precision in Phase 3

for name, scores in [("Model only", model_scores), ("Ensemble (model + anomaly)", ensemble_scores)]:
    preds = (scores >= THRESHOLD).astype(int)
    precision = precision_score(y_test, preds, zero_division=0)
    recall = recall_score(y_test, preds, zero_division=0)
    pr_auc = average_precision_score(y_test, scores)
    print(f"\n{name}:")
    print(f"  Precision: {precision:.4f} | Recall: {recall:.4f} | PR-AUC: {pr_auc:.4f}")

test_df["ensemble_score"] = ensemble_scores
test_df["model_score"] = model_scores
test_df.to_parquet("data/test_with_scores.parquet", index=False)
print("\nSaved scored test set to data/test_with_scores.parquet")