from collections.abc import Iterator

import numpy as np
import pytest
from fastapi.testclient import TestClient


class FakeModel:
    """Substitui o Pipeline real nos testes — sem precisar do MLflow vivo."""

    def __init__(self, fraud_probability: float = 0.0) -> None:
        self.fraud_probability = fraud_probability

    def predict_proba(self, X: object) -> np.ndarray:
        return np.array([[1 - self.fraud_probability, self.fraud_probability]])


@pytest.fixture
def api_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Client de teste com o modelo real substituído por um FakeModel legítimo."""
    monkeypatch.setattr("app.main.mlflow.sklearn.load_model", lambda uri: FakeModel())
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def fraud_api_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Client de teste com o FakeModel sempre prevendo fraude (probability=0.99)."""
    monkeypatch.setattr(
        "app.main.mlflow.sklearn.load_model", lambda uri: FakeModel(fraud_probability=0.99)
    )
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def sample_transaction() -> dict:
    """Transação sintética para testes unitários (sem dependência de dados reais)."""
    return {
        "Time": 0.0,
        "V1": -1.359807,
        "V2": -0.072781,
        "V3": 2.536347,
        "V4": 1.378155,
        "V5": -0.338321,
        "V6": 0.462388,
        "V7": 0.239599,
        "V8": 0.098698,
        "V9": 0.363787,
        "V10": 0.090794,
        "V11": -0.551600,
        "V12": -0.617801,
        "V13": -0.991390,
        "V14": -0.311169,
        "V15": 1.468177,
        "V16": -0.470401,
        "V17": 0.207971,
        "V18": 0.025791,
        "V19": 0.403993,
        "V20": 0.251412,
        "V21": -0.018307,
        "V22": 0.277838,
        "V23": -0.110474,
        "V24": 0.066928,
        "V25": 0.128539,
        "V26": -0.189115,
        "V27": 0.133558,
        "V28": -0.021053,
        "Amount": 149.62,
    }


@pytest.fixture
def api_payload(sample_transaction: dict) -> dict:
    """Mesma transação, sem 'Time' — o schema Transaction da API não conhece esse campo."""
    return {key: value for key, value in sample_transaction.items() if key != "Time"}
