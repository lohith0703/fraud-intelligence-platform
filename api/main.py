import pandas as pd
import xgboost as xgb
import shap
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Fraud Intelligence API")

print("Loading model...")
model = xgb.XGBClassifier()
model.load_model("ml/fraud_model.json")
explainer = shap.TreeExplainer(model)

FEATURE_COLS_NUMERIC = [
    "account_velocity", "amount_deviation", "balance_mismatch",
    "is_new_destination", "dest_velocity", "amount"
]
TYPE_COLS = ["type_CASH_IN", "type_CASH_OUT", "type_DEBIT", "type_PAYMENT", "type_TRANSFER"]
ALL_FEATURE_COLS = FEATURE_COLS_NUMERIC + TYPE_COLS
THRESHOLD = 0.8485  # our chosen ~80% recall / ~56% precision operating point


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

    score = float(model.predict_proba(X)[:, 1][0])
    is_flagged = score >= THRESHOLD

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
        "risk_score": round(score, 4),
        "flagged": is_flagged,
        "threshold_used": THRESHOLD,
        "top_reasons": top_reasons,
    }