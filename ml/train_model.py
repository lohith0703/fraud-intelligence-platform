import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    precision_score, recall_score, f1_score,
    average_precision_score, confusion_matrix, classification_report,
    precision_recall_curve
)

print("Loading train/test data...")
train_df = pd.read_parquet("data/train.parquet")
test_df = pd.read_parquet("data/test.parquet")

# One-hot encode transaction type (categorical -> numeric columns the model can use)
feature_cols_numeric = [
    "account_velocity", "amount_deviation", "balance_mismatch",
    "is_new_destination", "dest_velocity", "amount"
]

train_encoded = pd.get_dummies(train_df, columns=["type"], prefix="type")
test_encoded = pd.get_dummies(test_df, columns=["type"], prefix="type")

# Align columns in case a type appears in one set but not the other
train_encoded, test_encoded = train_encoded.align(test_encoded, join="left", axis=1, fill_value=0)

type_cols = [c for c in train_encoded.columns if c.startswith("type_")]
feature_cols = feature_cols_numeric + type_cols

X_train = train_encoded[feature_cols].astype(float)
y_train = train_encoded["is_fraud"].astype(int)
X_test = test_encoded[feature_cols].astype(float)
y_test = test_encoded["is_fraud"].astype(int)

print(f"Features used: {feature_cols}")
print(f"Train shape: {X_train.shape} | Test shape: {X_test.shape}")

# Handle severe class imbalance: weight positive (fraud) class up
scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()
print(f"scale_pos_weight: {scale_pos_weight:.1f}")

model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.1,
    scale_pos_weight=scale_pos_weight,
    eval_metric="aucpr",
    random_state=42,
)

print("Training model...")
model.fit(X_train, y_train)

print("\nEvaluating on held-out (chronologically later) test set...")
y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
pr_auc = average_precision_score(y_test, y_proba)

print(f"\nPrecision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 Score:  {f1:.4f}")
print(f"PR-AUC:    {pr_auc:.4f}")

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nFull classification report:")
print(classification_report(y_test, y_pred, digits=4))

precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)
print("\nPrecision/Recall at a few example thresholds:")
for target_recall in [0.5, 0.7, 0.8, 0.9, 0.95]:
    idx = (abs(recalls - target_recall)).argmin()
    print(f"  ~Recall={recalls[idx]:.3f} -> Precision={precisions[idx]:.4f} (threshold={thresholds[min(idx, len(thresholds)-1)]:.4f})")

model.save_model("ml/fraud_model.json")
print("\nModel saved to ml/fraud_model.json")