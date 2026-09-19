FROM python:3.13-slim

WORKDIR /app

COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY ml/fraud_model.json ./ml/fraud_model.json
COPY ml/anomaly_detector.joblib ./ml/anomaly_detector.joblib

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]