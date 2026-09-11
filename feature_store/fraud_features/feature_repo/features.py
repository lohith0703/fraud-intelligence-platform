from datetime import timedelta
from feast import Entity, FeatureView, Field
from feast.types import Float64
from feast.value_type import ValueType
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import PostgreSQLSource

account = Entity(
    name="account_id",
    join_keys=["orig_account_id"],
    value_type=ValueType.STRING,
    description="A PaySim account (sender side of a transaction)",
)
transactions_source = PostgreSQLSource(
    name="transactions_source",
    query="SELECT orig_account_id, step, amount, created_at AS event_timestamp FROM transactions",
    timestamp_field="event_timestamp",
)

account_features = FeatureView(
    name="account_features",
    entities=[account],
    ttl=timedelta(days=1),
    schema=[
        Field(name="amount", dtype=Float64),
    ],
    online=True,
    source=transactions_source,
)