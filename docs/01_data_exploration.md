# Data Exploration Findings — PaySim1

Dataset: ealaxi/paysim1 (Kaggle)
Rows: 6,362,620 | Columns: 11

## Class balance
- Fraud rate: 0.1291% (8,213 fraud / 6,362,620 total)
- Severe class imbalance -> precision/recall/PR-AUC required, accuracy is misleading

## Fraud by transaction type
- TRANSFER: 0.769% fraud rate
- CASH_OUT: 0.184% fraud rate
- PAYMENT, CASH_IN, DEBIT: 0% fraud rate
-> Fraud concentrated in money-movement transaction types

## Baseline rule performance (isFlaggedFraud)
- Fired 16 times total, against 8,213 actual fraud cases
- Naive threshold rule is not a viable detector on its own
- Justifies ML + anomaly detection + graph-based approach

## Known data leakage risk
- oldbalanceOrg/newbalanceOrig/oldbalanceDest/newbalanceDest are unreliable for
  fraudulent transactions because flagged transactions are cancelled in the simulation
- Raw balance columns will NOT be used directly as model features;
  derived/delta features will be engineered instead
