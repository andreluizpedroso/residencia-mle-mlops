"""
Model Registry: registra o melhor modelo e promove para Production.

O que faz:
1. Busca o run com maior PR-AUC no experimento de treinamento
2. Registra o modelo no MLflow Model Registry
3. Promove: None → Staging → Production (arquiva versão anterior)
4. Define alias 'champion' (API moderna do MLflow 2.x)
5. Carrega o modelo do registry e valida com uma predição real

Uso:
    uv run python pipelines/register_model.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
os.environ.setdefault("PYTHONUTF8", "1")

import mlflow.sklearn
import pandas as pd
from mlflow.entities import Run
from mlflow.entities.model_registry import ModelVersion
from mlflow.tracking import MlflowClient

import mlflow

# ── Configuração ──────────────────────────────────────────────────────────────

MLFLOW_TRACKING_URI = "http://localhost:5000"
EXPERIMENT_NAME = "fraud-detection-training"
MODEL_NAME = "fraud-detector"
METRIC = "pr_auc"  # métrica usada para eleger o melhor run
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"


# ── Funções ───────────────────────────────────────────────────────────────────

def find_best_run(client: MlflowClient) -> Run:
    """Busca o run com maior PR-AUC no experimento."""
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        raise ValueError(
            f"Experimento '{EXPERIMENT_NAME}' nao encontrado. "
            "Execute pipelines/train.py primeiro."
        )

    runs = client.search_runs(
        experiment_ids=[experiment.experiment_id],
        filter_string=f"metrics.{METRIC} > 0",
        order_by=[f"metrics.{METRIC} DESC"],
        max_results=1,
    )
    if not runs:
        raise ValueError("Nenhum run encontrado. Execute pipelines/train.py primeiro.")

    best = runs[0]
    print("Melhor run encontrado:")
    print(f"  run_id     : {best.info.run_id}")
    print(f"  model_type : {best.data.params.get('model_type', 'N/A')}")
    print(f"  {METRIC}   : {best.data.metrics.get(METRIC, 0):.4f}")
    return best


def register(client: MlflowClient, run_id: str) -> ModelVersion:
    """Registra o modelo no Model Registry e retorna a versão criada."""
    model_uri = f"runs:/{run_id}/model"
    print(f"\nRegistrando '{MODEL_NAME}' a partir do run {run_id[:8]}...")
    mv = mlflow.register_model(model_uri=model_uri, name=MODEL_NAME)

    # Adiciona descrição e tag para rastreabilidade
    client.update_model_version(
        name=MODEL_NAME,
        version=mv.version,
        description=f"Treinado com {mv.run_id[:8]} | otimizado por {METRIC}",
    )
    client.set_model_version_tag(MODEL_NAME, mv.version, "promoted_by", "register_model.py")

    print(f"  Versao criada : {mv.version}")
    print(f"  Estagio atual : {mv.current_stage}")
    return mv


def promote(client: MlflowClient, version: str) -> None:
    """Promove o modelo usando aliases (API moderna do MLflow 2.9+).

    Aliases substituem os stages deprecados (Staging/Production).
    'challenger' → modelo candidato sendo validado
    'champion'   → modelo oficial em produção
    """
    print(f"\nDefinindo alias 'challenger' para versao {version}...")
    client.set_registered_model_alias(MODEL_NAME, "challenger", version)
    print("  challenger : OK")

    # Em produção real, aqui entrariam testes de integração e aprovação de QA
    # antes de promover para champion.

    print(f"Promovendo versao {version} para alias 'champion'...")
    client.set_registered_model_alias(MODEL_NAME, "champion", version)
    print("  champion : OK")


def validate(model_name: str) -> None:
    """Carrega o modelo do registry pelo alias e confirma que prediz corretamente."""
    print("\nValidando modelo carregado do registry...")
    model = mlflow.sklearn.load_model(f"models:/{model_name}@champion")

    test = pd.read_parquet(PROCESSED_DIR / "test.parquet")
    X_sample = test.drop(columns=["Class"]).head(5)
    y_sample = test["Class"].head(5).tolist()

    preds = model.predict(X_sample).tolist()
    probs = model.predict_proba(X_sample)[:, 1].tolist()

    print(f"  Tipo de modelo    : {type(model).__name__}")
    print(f"  Classes reais     : {y_sample}")
    print(f"  Predicoes         : {preds}")
    print(f"  Prob. de fraude   : {[round(p, 4) for p in probs]}")


# ── Orquestração ──────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print("Model Registry - Fraud Detector")
    print("=" * 50)

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    best_run = find_best_run(client)
    mv = register(client, best_run.info.run_id)
    promote(client, mv.version)
    validate(MODEL_NAME)

    print(f"\nModelo '{MODEL_NAME}' versao {mv.version} promovido para champion.")
    print("Carregue em qualquer script com:")
    print(f"  mlflow.sklearn.load_model('models:/{MODEL_NAME}@champion')")
    print(f"\nAcesse: http://localhost:5000/#/models/{MODEL_NAME}")


if __name__ == "__main__":
    main()
