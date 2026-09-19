import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "Fraud Intelligence API is running"


def test_score_known_fraud_transaction():
    """Verifies the model correctly flags a transaction we already know is fraud
    (transaction_id 5115795, verified in Phase 3 SHAP analysis)."""
    payload = {
        "transaction_id": 5115795,
        "type": "TRANSFER",
        "amount": 7360.15,
        "account_velocity": 1,
        "amount_deviation": 0.0,
        "balance_mismatch": False,
        "is_new_destination": True,
        "dest_velocity": 1
    }
    response = client.post("/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["model_score"] > 0.9
    assert data["flagged"] is True


def test_score_response_has_required_fields():
    payload = {
        "transaction_id": 1,
        "type": "PAYMENT",
        "amount": 100.0,
        "account_velocity": 1,
        "amount_deviation": 0.0,
        "balance_mismatch": False,
        "is_new_destination": True,
        "dest_velocity": 1
    }
    response = client.post("/score", json=payload)
    data = response.json()
    for field in ["model_score", "anomaly_score", "ensemble_score", "flagged", "top_reasons"]:
        assert field in data