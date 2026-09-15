import pandas as pd
import numpy as np

def calculate_psi(reference, current, buckets=10):
    """
    PSI compares a reference distribution against a current one, bucketed into
    deciles based on the reference data, then measures how much the proportion
    of data in each bucket has shifted.
    """
    breakpoints = np.percentile(reference, np.linspace(0, 100, buckets + 1))
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf

    ref_counts, _ = np.histogram(reference, bins=breakpoints)
    cur_counts, _ = np.histogram(current, bins=breakpoints)

    ref_pct = ref_counts / len(reference)
    cur_pct = cur_counts / len(current)

    # Avoid division by zero / log(0) for empty buckets
    ref_pct = np.where(ref_pct == 0, 0.0001, ref_pct)
    cur_pct = np.where(cur_pct == 0, 0.0001, cur_pct)

    psi = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
    return psi


print("Loading train (reference) and test (current) data...")
train_df = pd.read_parquet("data/train.parquet")
test_df = pd.read_parquet("data/test.parquet")

features_to_check = ["amount", "amount_deviation", "dest_velocity"]

print("\nPSI results (reference = train, current = test):")
print(f"{'Feature':<20} {'PSI':>8}   Interpretation")
print("-" * 60)

for feat in features_to_check:
    psi = calculate_psi(train_df[feat].values, test_df[feat].values)
    if psi < 0.1:
        interpretation = "No significant shift"
    elif psi < 0.25:
        interpretation = "Moderate shift -- monitor"
    else:
        interpretation = "Significant shift -- consider retraining"
    print(f"{feat:<20} {psi:>8.4f}   {interpretation}")

# Also directly check fraud rate shift, since we already know this one is real
train_fraud_rate = train_df["is_fraud"].mean()
test_fraud_rate = test_df["is_fraud"].mean()
print(f"\nFraud rate -- train: {train_fraud_rate*100:.4f}% | test: {test_fraud_rate*100:.4f}% "
      f"| ratio: {test_fraud_rate/train_fraud_rate:.2f}x")

# PSI on raw features doesn't capture shifts in the feature-label relationship
# (concept drift) -- only shifts in the features' own distribution. For a
# skewed binary variable like is_fraud, percentile-based bucketing breaks down
# (most percentiles collapse to the same value), so we compute PSI directly
# on the two explicit categories (fraud / not fraud) instead.
def calculate_psi_binary(reference, current):
    ref_fraud_pct = np.clip(reference.mean(), 0.0001, 0.9999)
    cur_fraud_pct = np.clip(current.mean(), 0.0001, 0.9999)
    ref_dist = np.array([1 - ref_fraud_pct, ref_fraud_pct])
    cur_dist = np.array([1 - cur_fraud_pct, cur_fraud_pct])
    return np.sum((cur_dist - ref_dist) * np.log(cur_dist / ref_dist))

psi_fraud_rate = calculate_psi_binary(
    train_df["is_fraud"].values.astype(float),
    test_df["is_fraud"].values.astype(float),
)
print(f"\nPSI on is_fraud (binary-correct method): {psi_fraud_rate:.4f} "
      f"(captures the label-rate shift that feature-level PSI missed)")