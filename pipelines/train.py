"""
Pipeline de treinamento: treina classificadores e rastreia experimentos no MLflow.

Uso:
    uv run python pipelines/train.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
os.environ.setdefault("PYTHONUTF8", "1")

import matplotlib
matplotlib.use("Agg")  # sem display — funciona em CI e Docker

import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
import numpy as np
from mlflow.models import infer_signature
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

# ── Configuração ──────────────────────────────────────────────────────────────

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
PLOTS_DIR = Path(__file__).parent.parent / "data" / "artifacts"
MLFLOW_TRACKING_URI = "http://localhost:5000"
EXPERIMENT_NAME = "fraud-detection-training"
RANDOM_STATE = 42
TARGET = "Class"

# Dois modelos para comparar no mesmo experimento MLflow
MODELS: dict[str, ClassifierMixin] = {
    "logistic_regression": LogisticRegression(
        class_weight="balanced",  # penaliza erros em fraude proporcionalmente
        max_iter=1000,
        random_state=RANDOM_STATE,
        C=1.0,
    ),
    "random_forest": RandomForestClassifier(
        n_estimators=100,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,  # usa todos os núcleos disponíveis
    ),
}


# ── Funções ───────────────────────────────────────────────────────────────────

def load_data() -> tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """Carrega os dados processados pela feature engineering."""
    train = pd.read_parquet(PROCESSED_DIR / "train.parquet")
    test = pd.read_parquet(PROCESSED_DIR / "test.parquet")

    X_train = train.drop(columns=[TARGET])
    y_train = train[TARGET]
    X_test = test.drop(columns=[TARGET])
    y_test = test[TARGET]

    print(f"Treino : {X_train.shape[0]:,} amostras | {X_train.shape[1]} features")
    print(f"Teste  : {X_test.shape[0]:,} amostras")
    return X_train, y_train, X_test, y_test


def compute_metrics(
    y_true: pd.Series,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
) -> dict[str, float]:
    """Calcula as métricas relevantes para detecção de fraude."""
    return {
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall":    round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1":        round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc":   round(float(roc_auc_score(y_true, y_prob)), 4),
        "pr_auc":    round(float(average_precision_score(y_true, y_prob)), 4),
    }


def save_confusion_matrix(
    y_true: pd.Series,
    y_pred: np.ndarray,
    model_name: str,
) -> Path:
    """Gera e salva a matriz de confusão como imagem."""
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay(cm, display_labels=["Legitima", "Fraude"]).plot(
        ax=ax, colorbar=False
    )
    ax.set_title(f"Confusion Matrix - {model_name}")
    path = PLOTS_DIR / f"confusion_matrix_{model_name}.png"
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def train_and_log(
    name: str,
    model: ClassifierMixin,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> str:
    """Treina um modelo e loga params, métricas e artefatos no MLflow."""
    print(f"\n[{name}] Treinando...")

    with mlflow.start_run(run_name=name) as run:
        model.fit(X_train, y_train)

        y_pred: np.ndarray = model.predict(X_test)  # type: ignore[assignment]
        y_prob: np.ndarray = model.predict_proba(X_test)[:, 1]  # type: ignore[union-attr]

        metrics = compute_metrics(y_test, y_pred, y_prob)

        # Assinatura: schema de entrada (features) + saída (predições)
        # Resolve o warning "Model logged without a signature"
        signature = infer_signature(X_test, y_pred)
        input_example = X_test.head(5)

        mlflow.log_params({"model_type": name, **model.get_params()})  # type: ignore[union-attr]
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            signature=signature,
            input_example=input_example,
        )

        cm_path = save_confusion_matrix(y_test, y_pred, name)
        mlflow.log_artifact(str(cm_path), artifact_path="plots")

        print(classification_report(y_test, y_pred, target_names=["Legitima", "Fraude"]))
        for metric_name, value in metrics.items():
            print(f"  {metric_name} : {value:.4f}")

        return run.info.run_id


# ── Orquestração ──────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print("Pipeline de Treinamento - Fraud Detection")
    print("=" * 50)

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    X_train, y_train, X_test, y_test = load_data()

    run_ids: dict[str, str] = {}
    for name, model in MODELS.items():
        run_id = train_and_log(name, model, X_train, y_train, X_test, y_test)
        run_ids[name] = run_id

    print("\nRuns gerados:")
    for name, run_id in run_ids.items():
        print(f"  {name}: {run_id}")

    print("\nTreinamento concluido.")
    print("Acesse: http://localhost:5000")


if __name__ == "__main__":
    main()
