"""Testes para o Feature Store (Feast)."""

from pathlib import Path

import numpy as np
import pandas as pd


def _make_raw_csv(path: Path, n: int = 20) -> None:
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "Time": range(n),
        **{f"V{i}": rng.normal(size=n) for i in range(1, 29)},
        "Amount": rng.exponential(scale=100, size=n),
        "Class": [0] * (n - 1) + [1],
    })
    df.to_csv(path, index=False)


def test_prepare_feast_data_adds_required_columns(tmp_path: Path) -> None:
    from pipelines.materialize_features import prepare_feast_data

    raw = tmp_path / "creditcard.csv"
    _make_raw_csv(raw, n=20)

    output = prepare_feast_data(raw, tmp_path / "feast")
    result = pd.read_parquet(output)

    assert "transaction_id" in result.columns
    assert "event_timestamp" in result.columns
    assert "Time" not in result.columns
    assert len(result) == 20


def test_prepare_feast_data_transaction_ids_are_unique(tmp_path: Path) -> None:
    from pipelines.materialize_features import prepare_feast_data

    raw = tmp_path / "creditcard.csv"
    _make_raw_csv(raw, n=50)

    output = prepare_feast_data(raw, tmp_path / "feast")
    result = pd.read_parquet(output)

    assert result["transaction_id"].nunique() == 50


def test_feature_view_schema_has_all_columns() -> None:
    from feature_store.features import transaction_features

    names = [f.name for f in transaction_features.schema]
    assert "Amount" in names
    assert "V1" in names
    assert "V28" in names
    assert "Class" in names
    assert len(names) == 30  # V1–V28 + Amount + Class
