import pandas as pd
import xgboost as xgb
import shap
import joblib
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Fraud Intelligence API")

print("Loading model, anomaly detector, and explainer...")
model = xgb.XGBClassifier()
model.load_model("ml/fraud_model.json")
iso_forest = joblib.load("ml/anomaly_detector.joblib")
explainer = shap.TreeExplainer(model)

FEATURE_COLS_NUMERIC = [
    "account_velocity", "amount_deviation", "balance_mismatch",
    "is_new_destination", "dest_velocity", "amount"
]
TYPE_COLS = ["type_CASH_IN", "type_CASH_OUT", "type_DEBIT", "type_PAYMENT", "type_TRANSFER"]
ALL_FEATURE_COLS = FEATURE_COLS_NUMERIC + TYPE_COLS
THRESHOLD = 0.8485  # ~80% recall / ~56% precision operating point (model-only score scale)

# Deliberate, low weight on the anomaly detector -- reflects its measured near-zero
# overlap with known fraud (docs/05_anomaly_detection_notes.md). Kept as insurance
# against novel fraud patterns not present in current labels, not a performance booster.
MODEL_WEIGHT = 0.9
ANOMALY_WEIGHT = 0.1

# Rough min/max bounds from Phase 3's test-set anomaly scores, used to normalize
# live anomaly scores into the same 0-1 range the ensemble expects.
ANOMALY_SCORE_MIN = -0.2
ANOMALY_SCORE_MAX = 0.2


class Transaction(BaseModel):
    transaction_id: int
    type: str
    amount: float
    account_velocity: int
    amount_deviation: float
    balance_mismatch: bool
    is_new_destination: bool
    dest_velocity: int


@app.get("/")
def root():
    return {"status": "Fraud Intelligence API is running"}


@app.post("/score")
def score_transaction(txn: Transaction):
    row = {col: 0.0 for col in ALL_FEATURE_COLS}
    row["account_velocity"] = txn.account_velocity
    row["amount_deviation"] = txn.amount_deviation
    row["balance_mismatch"] = float(txn.balance_mismatch)
    row["is_new_destination"] = float(txn.is_new_destination)
    row["dest_velocity"] = txn.dest_velocity
    row["amount"] = txn.amount
    type_col = f"type_{txn.type}"
    if type_col in row:
        row[type_col] = 1.0

    X = pd.DataFrame([row])[ALL_FEATURE_COLS]

    # Supervised model score
    model_score = float(model.predict_proba(X)[:, 1][0])

    # Anomaly score, normalized to roughly 0-1 using Phase 3's observed range
    X_anomaly = X[FEATURE_COLS_NUMERIC]
    raw_anomaly = -iso_forest.decision_function(X_anomaly)[0]
    anomaly_score = float(np.clip(
        (raw_anomaly - ANOMALY_SCORE_MIN) / (ANOMALY_SCORE_MAX - ANOMALY_SCORE_MIN), 0, 1
    ))

    ensemble_score = MODEL_WEIGHT * model_score + ANOMALY_WEIGHT * anomaly_score
    is_flagged = model_score >= THRESHOLD  # decision still uses the model-only threshold; see docs/08

    shap_values = explainer.shap_values(X)[0]
    contributions = sorted(
        zip(ALL_FEATURE_COLS, shap_values), key=lambda x: abs(x[1]), reverse=True
    )
    top_reasons = [
        {"feature": feat, "impact": round(float(val), 4)}
        for feat, val in contributions[:5]
    ]

    return {
        "transaction_id": txn.transaction_id,
        "model_score": round(model_score, 4),
        "anomaly_score": round(anomaly_score, 4),
        "ensemble_score": round(ensemble_score, 4),
        "flagged": is_flagged,
        "threshold_used": THRESHOLD,
        "top_reasons": top_reasons,
    }