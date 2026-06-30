"""Testes da API de serving (app/main.py).

O modelo MLflow real é substituído por um FakeModel (ver tests/conftest.py)
para que os testes rodem em qualquer máquina/CI sem depender da stack
MLflow + PostgreSQL + MinIO estar de pé.
"""

from fastapi.testclient import TestClient


def test_health_reports_model_loaded(api_client: TestClient) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "model_loaded": True,
        "model_alias": "champion",
    }


def test_predict_legitimate_transaction(api_client: TestClient, api_payload: dict) -> None:
    response = api_client.post("/predict", json=api_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["is_fraud"] is False
    assert body["fraud_probability"] == 0.0
    assert body["model_alias"] == "champion"


def test_predict_fraud_transaction(fraud_api_client: TestClient, api_payload: dict) -> None:
    response = fraud_api_client.post("/predict", json=api_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["is_fraud"] is True
    assert body["fraud_probability"] == 0.99


def test_predict_rejects_missing_fields(api_client: TestClient) -> None:
    response = api_client.post("/predict", json={"V1": 0.1, "Amount": 10.0})

    assert response.status_code == 422
    missing_fields = {error["loc"][-1] for error in response.json()["detail"]}
    assert "V2" in missing_fields


def test_predict_rejects_negative_amount(api_client: TestClient, api_payload: dict) -> None:
    api_payload["Amount"] = -50.0

    response = api_client.post("/predict", json=api_payload)

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(error["loc"][-1] == "Amount" for error in errors)
