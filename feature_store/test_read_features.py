from feast import FeatureStore

store = FeatureStore(repo_path="feature_store/fraud_features/feature_repo")

feature_vector = store.get_online_features(
    features=[
        "account_features:account_velocity",
        "account_features:amount_deviation",
        "account_features:balance_mismatch",
        "account_features:is_new_destination",
    ],
    entity_rows=[{"orig_account_id": "C278476563"}],
).to_dict()

print(feature_vector)