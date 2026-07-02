"""
Definições de features para o Feature Store (Feast).

Entidade: transaction_id — identifica cada transação de forma única.
FeatureView: transaction_features — V1-V28, Amount e Class.

Estas definições são a fonte de verdade: treino e serving leem
do mesmo lugar, com a mesma lógica, sem risco de dessincronização.
"""

from datetime import timedelta
from pathlib import Path

from feast import Entity, FeatureView, Field, FileSource
from feast.types import Float64, Int64
from feast.value_type import ValueType

FEAST_DATA = Path(__file__).parent.parent / "data" / "feast"

# Fonte de dados offline: parquet gerado por materialize_features.py
transaction_source = FileSource(
    path=str(FEAST_DATA / "transactions.parquet"),
    timestamp_field="event_timestamp",
)

# Entidade: a "chave primária" do Feature Store
transaction = Entity(
    name="transaction_id",
    description="ID unico de cada transacao",
    value_type=ValueType.INT64,
)

# Feature View: agrupa todas as features de uma transação
transaction_features = FeatureView(
    name="transaction_features",
    entities=[transaction],
    ttl=timedelta(days=365),
    schema=[
        *[Field(name=f"V{i}", dtype=Float64) for i in range(1, 29)],
        Field(name="Amount", dtype=Float64),
        Field(name="Class", dtype=Int64),
    ],
    source=transaction_source,
)
