import pandas as pd
import xgboost as xgb
import shap

print("Loading model and test data...")
model = xgb.XGBClassifier()
model.load_model("ml/fraud_model.json")

test_df = pd.read_parquet("data/test.parquet")

feature_cols_numeric = [
    "account_velocity", "amount_deviation", "balance_mismatch",
    "is_new_destination", "dest_velocity", "amount"
]
test_encoded = pd.get_dummies(test_df, columns=["type"], prefix="type")
type_cols = [c for c in test_encoded.columns if c.startswith("type_")]
feature_cols = feature_cols_numeric + type_cols

X_test = test_encoded[feature_cols].astype(float)
y_proba = model.predict_proba(X_test)[:, 1]

test_df = test_df.reset_index(drop=True)
test_df["predicted_score"] = y_proba

# A high-confidence true positive, a borderline case near our chosen threshold,
# and a false positive -- more varied and demo-worthy than only extreme saturated cases
high_conf_tp = test_df[(test_df["is_fraud"] == True) & (test_df["predicted_score"] > 0.99)].head(1)
borderline = test_df[(test_df["predicted_score"] > 0.85) & (test_df["predicted_score"] < 0.95)].head(1)
false_positive = test_df[(test_df["is_fraud"] == False) & (test_df["predicted_score"] > 0.9)].head(1)

top_flagged = pd.concat([high_conf_tp, borderline, false_positive])
print("\nSelected varied examples (high-confidence TP, borderline case, false positive):")
print(top_flagged[["transaction_id", "type", "amount", "predicted_score", "is_fraud"]])

print("\nComputing SHAP values (this explains each individual prediction)...")
explainer = shap.TreeExplainer(model)

indices = top_flagged.index
shap_values = explainer.shap_values(X_test.loc[indices])

for i, idx in enumerate(indices):
    row = test_df.loc[idx]
    print(f"\n--- Transaction {row['transaction_id']} "
          f"(type={row['type']}, amount={row['amount']:.2f}, "
          f"score={row['predicted_score']:.4f}, actual_fraud={row['is_fraud']}) ---")

    contributions = list(zip(feature_cols, shap_values[i]))
    contributions.sort(key=lambda x: abs(x[1]), reverse=True)

    print("Top contributing features:")
    for feat, val in contributions[:5]:
        direction = "increased" if val > 0 else "decreased"
        print(f"  {feat}: {direction} risk score by {abs(val):.4f}")