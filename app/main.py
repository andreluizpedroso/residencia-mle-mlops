"""
API de detecção de fraude: serve o modelo `fraud-detector@champion` via REST.

O modelo é carregado uma única vez no startup (lifespan) e fica em memória
para todas as requisições — carregar do MinIO a cada request seria lento
demais para um sistema que precisa responder em milissegundos.

Uso (local):
    uv run uvicorn app.main:app --reload --port 8000

Docs interativas:
    http://localhost:8000/docs
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
os.environ.setdefault("PYTHONUTF8", "1")

import mlflow
import mlflow.sklearn
import pandas as pd
from fastapi import FastAPI, HTTPException

from app.schemas import HealthResponse, PredictionResponse, Transaction

# ── Configuração ──────────────────────────────────────────────────────────────

# "localhost" funciona rodando fora do Docker; dentro do compose, o serviço
# sobrescreve essa variável para "http://mlflow:5000" (nome do serviço na rede).
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
MODEL_NAME = "fraud-detector"
MODEL_ALIAS = "champion"
MODEL_URI = f"models:/{MODEL_NAME}@{MODEL_ALIAS}"

ml_models: dict[str, object] = {}


# ── Ciclo de vida da aplicação ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Carrega o modelo do Model Registry quando a API sobe."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    print(f"Carregando modelo: {MODEL_URI}")
    ml_models["fraud_detector"] = mlflow.sklearn.load_model(MODEL_URI)
    print("Modelo carregado com sucesso.")

    yield  # API fica disponível aqui

    ml_models.clear()


app = FastAPI(
    title="Fraud Detection API",
    description="Detecta fraude em transações de cartão de crédito em tempo real.",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Verifica se a API está no ar e se o modelo está carregado."""
    return HealthResponse(
        status="ok",
        model_loaded="fraud_detector" in ml_models,
        model_alias=MODEL_ALIAS,
    )


@app.post("/predict", response_model=PredictionResponse)
def predict(transaction: Transaction) -> PredictionResponse:
    """Recebe uma transação e retorna se é fraude e a probabilidade."""
    model = ml_models.get("fraud_detector")
    if model is None:
        raise HTTPException(status_code=503, detail="Modelo nao carregado.")

    df = pd.DataFrame([transaction.model_dump()])
    probability = float(model.predict_proba(df)[0, 1])  # type: ignore[union-attr]

    return PredictionResponse(
        is_fraud=probability >= 0.5,
        fraud_probability=round(probability, 4),
        model_alias=MODEL_ALIAS,
    )
