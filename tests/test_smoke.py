"""Smoke tests — validam que o ambiente básico está funcional."""

import importlib

from packaging.version import Version


def test_mlflow_importable() -> None:
    mlflow = importlib.import_module("mlflow")
    assert Version(mlflow.__version__) >= Version("2.15.0")


def test_sklearn_importable() -> None:
    sklearn = importlib.import_module("sklearn")
    assert Version(sklearn.__version__) >= Version("1.5.0")


def test_sample_transaction_schema(sample_transaction: dict) -> None:
    expected_keys = {f"V{i}" for i in range(1, 29)} | {"Time", "Amount"}
    assert expected_keys == set(sample_transaction.keys())
    assert all(isinstance(v, float) for v in sample_transaction.values())
