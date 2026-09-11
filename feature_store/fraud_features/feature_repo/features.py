from datetime import timedelta
from feast import Entity, FeatureView, Field, PushSource
from feast.types import Float64, Int64, Bool
from feast.value_type import ValueType
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import PostgreSQLSource

account = Entity(
    name="account_id",
    join_keys=["orig_account_id"],
    value_type=ValueType.STRING,
    description="A PaySim account (sender side of a transaction)",
)

transactions_batch_source = PostgreSQLSource(
    name="transactions_source",
    query="SELECT orig_account_id, step, amount, created_at AS event_timestamp FROM transactions",
    timestamp_field="event_timestamp",
)

transactions_push_source = PushSource(
    name="transactions_push_source",
    batch_source=transactions_batch_source,
)

account_features = FeatureView(
    name="account_features",
    entities=[account],
    ttl=timedelta(days=1),
    schema=[
        Field(name="account_velocity", dtype=Int64),
        Field(name="amount_deviation", dtype=Float64),
        Field(name="balance_mismatch", dtype=Bool),
        Field(name="is_new_destination", dtype=Bool),
    ],
    online=True,
    source=transactions_push_source,
)