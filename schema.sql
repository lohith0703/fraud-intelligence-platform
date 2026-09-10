CREATE TABLE accounts (
    account_id VARCHAR(20) PRIMARY KEY,
    account_type VARCHAR(10) NOT NULL  -- 'customer' or 'merchant'
);

CREATE TABLE transactions (
    transaction_id BIGSERIAL PRIMARY KEY,
    step INT NOT NULL,
    type VARCHAR(20) NOT NULL,
    amount NUMERIC(18, 2) NOT NULL,
    orig_account_id VARCHAR(20) NOT NULL REFERENCES accounts(account_id),
    dest_account_id VARCHAR(20) NOT NULL REFERENCES accounts(account_id),
    oldbalance_orig NUMERIC(18, 2),
    newbalance_orig NUMERIC(18, 2),
    oldbalance_dest NUMERIC(18, 2),
    newbalance_dest NUMERIC(18, 2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fraud_labels (
    transaction_id BIGINT PRIMARY KEY REFERENCES transactions(transaction_id),
    is_fraud BOOLEAN NOT NULL,
    is_flagged_fraud BOOLEAN NOT NULL,
    labeled_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transactions_orig ON transactions(orig_account_id);
CREATE INDEX idx_transactions_dest ON transactions(dest_account_id);
CREATE INDEX idx_transactions_step ON transactions(step);