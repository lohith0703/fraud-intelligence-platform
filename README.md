# Real-Time Adaptive Fraud Intelligence Platform

A production-style data engineering and machine learning system for detecting
fraudulent financial transactions in real time.

Status: Phase 1 — Data Foundation (in progress)

## Architecture (planned)
Transaction Producer -> Kafka -> Feature Engineering -> ML + Graph Intelligence
-> Fraud Risk Engine -> FastAPI -> Dashboard -> Monitoring
