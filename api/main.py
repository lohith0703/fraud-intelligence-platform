import time
import pandas as pd
import xgboost as xgb
import shap
import joblib
import numpy as np
import psycopg2
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import os

app = FastAPI(title="Fraud Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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
THRESHOLD = 0.8485
HIGH_SEVERITY_THRESHOLD = 0.95

MODEL_WEIGHT = 0.9
ANOMALY_WEIGHT = 0.1
ANOMALY_SCORE_MIN = -0.2
ANOMALY_SCORE_MAX = 0.2

# Prometheus metrics
REQUEST_COUNT = Counter("fraud_api_requests_total", "Total scoring requests")
FLAGGED_COUNT = Counter("fraud_api_flagged_total", "Total transactions flagged as fraud")
REQUEST_LATENCY = Histogram("fraud_api_request_latency_seconds", "Request latency in seconds")




def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5433")),
        dbname="fraud_db",
        user="fraud_user", password="fraud_pass"
    )


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
    start_time = time.perf_counter()
    REQUEST_COUNT.inc()

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

    model_score = float(model.predict_proba(X)[:, 1][0])

    X_anomaly = X[FEATURE_COLS_NUMERIC]
    raw_anomaly = -iso_forest.decision_function(X_anomaly)[0]
    anomaly_score = float(np.clip(
        (raw_anomaly - ANOMALY_SCORE_MIN) / (ANOMALY_SCORE_MAX - ANOMALY_SCORE_MIN), 0, 1
    ))

    ensemble_score = MODEL_WEIGHT * model_score + ANOMALY_WEIGHT * anomaly_score
    is_flagged = model_score >= THRESHOLD

    shap_values = explainer.shap_values(X)[0]
    contributions = sorted(
        zip(ALL_FEATURE_COLS, shap_values), key=lambda x: abs(x[1]), reverse=True
    )
    top_reasons = [
        {"feature": feat, "impact": round(float(val), 4)}
        for feat, val in contributions[:5]
    ]

    alert_id = None
    if is_flagged:
        severity = "High" if model_score >= HIGH_SEVERITY_THRESHOLD else "Medium"
        top_reason_str = top_reasons[0]["feature"].replace("type_", "") if top_reasons else None

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT alert_id FROM alerts WHERE transaction_id = %s", (txn.transaction_id,))
        existing = cur.fetchone()
        if existing:
            alert_id = existing[0]
        else:
            cur.execute("""
                INSERT INTO alerts (transaction_id, model_score, ensemble_score, severity, top_reason)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING alert_id
            """, (txn.transaction_id, model_score, ensemble_score, severity, top_reason_str))
            alert_id = cur.fetchone()[0]
            conn.commit()
        cur.close()
        conn.close()

    if is_flagged:
        FLAGGED_COUNT.inc()
    REQUEST_LATENCY.observe(time.perf_counter() - start_time)

    return {
        "transaction_id": txn.transaction_id,
        "model_score": round(model_score, 4),
        "anomaly_score": round(anomaly_score, 4),
        "ensemble_score": round(ensemble_score, 4),
        "flagged": is_flagged,
        "alert_id": alert_id,
        "threshold_used": THRESHOLD,
        "top_reasons": top_reasons,
    }


@app.get("/alerts")
def get_alerts(status: str = None, limit: int = 50):
    conn = get_db_connection()
    cur = conn.cursor()
    if status:
        cur.execute("""
            SELECT alert_id, transaction_id, model_score, ensemble_score, severity, status, top_reason, created_at
            FROM alerts WHERE status = %s ORDER BY created_at DESC LIMIT %s
        """, (status, limit))
    else:
        cur.execute("""
            SELECT alert_id, transaction_id, model_score, ensemble_score, severity, status, top_reason, created_at
            FROM alerts ORDER BY created_at DESC LIMIT %s
        """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    columns = ["alert_id", "transaction_id", "model_score", "ensemble_score", "severity", "status", "top_reason", "created_at"]
    return [dict(zip(columns, [str(v) if not isinstance(v, (int, float, type(None))) else v for v in row])) for row in rows]


@app.patch("/alerts/{alert_id}")
def update_alert_status(alert_id: int, status: str):
    valid_statuses = {"open", "confirmed_fraud", "false_positive"}
    if status not in valid_statuses:
        return {"error": f"status must be one of {valid_statuses}"}

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE alerts SET status = %s WHERE alert_id = %s RETURNING alert_id", (status, alert_id))
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if updated is None:
        return {"error": f"alert_id {alert_id} not found"}
    return {"alert_id": alert_id, "new_status": status}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)