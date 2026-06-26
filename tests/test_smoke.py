"""Smoke tests — validam que o ambiente básico está funcional."""

import importlib


def test_mlflow_importable() -> None:
    mlflow = importlib.import_module("mlflow")
    assert mlflow.__version__ >= "2.15.0"


def test_sklearn_importable() -> None:
    sklearn = importlib.import_module("sklearn")
    assert sklearn.__version__ >= "1.5.0"


def test_sample_transaction_schema(sample_transaction: dict) -> None:
    expected_keys = {f"V{i}" for i in range(1, 29)} | {"Time", "Amount"}
    assert expected_keys == set(sample_transaction.keys())
    assert all(isinstance(v, float) for v in sample_transaction.values())
