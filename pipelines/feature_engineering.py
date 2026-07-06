"""
Pipeline de feature engineering: transforma dados brutos em features prontas para treino.

O que faz:
- Separa features (X) do target (y)
- Escala a coluna Amount (única feature com escala real)
- Remove a coluna Time (não é útil como está — seria útil como hora do dia, Sprint 2+)
- Divide em treino (80%) e teste (20%) com estratificação
- Salva em Parquet e loga no MLflow

Uso:
    uv run python pipelines/feature_engineering.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega credenciais do .env (AWS_ACCESS_KEY_ID, MLFLOW_S3_ENDPOINT_URL, etc.)
load_dotenv(Path(__file__).parent.parent / ".env")

# Força UTF-8 no terminal do Windows (evita erro com emojis do MLflow)
os.environ.setdefault("PYTHONUTF8", "1")

import mlflow
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# ── Configuração ──────────────────────────────────────────────────────────────

RAW_FILE = Path(__file__).parent.parent / "data" / "raw" / "creditcard.csv"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
RANDOM_STATE = 42
TEST_SIZE = 0.2

MLFLOW_TRACKING_URI = "http://localhost:5000"
EXPERIMENT_NAME = "fraud-detection-feature-engineering"


# ── Feature Engineering ───────────────────────────────────────────────────────

def load_raw(path: Path) -> pd.DataFrame:
    """Carrega o CSV bruto."""
    print(f"Carregando dados de: {path}")
    df = pd.read_csv(path)
    print(f"Shape: {df.shape} ({df.shape[0]:,} transações, {df.shape[1]} colunas)")
    return df


def report_class_balance(df: pd.DataFrame) -> dict[str, float]:
    """Calcula e exibe o desbalanceamento de classes."""
    counts = df["Class"].value_counts()
    fraud_pct = counts[1] / len(df) * 100
    print("\nDistribuição de classes:")
    print(f"  Legítimas : {counts[0]:,} ({100 - fraud_pct:.2f}%)")
    print(f"  Fraudes   : {counts[1]:,} ({fraud_pct:.4f}%)")
    return {"fraud_pct": round(fraud_pct, 4), "total_samples": len(df)}


def build_pipeline() -> Pipeline:
    """
    Cria o pipeline de pré-processamento.

    Amount é a única feature em escala real (reais/dólares).
    V1-V28 já são componentes PCA — sem escala.
    Time é descartado aqui (análise exploratória mostrou baixo poder preditivo bruto).
    """
    return Pipeline([
        ("scaler", StandardScaler()),
    ])


def engineer_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aplica feature engineering e retorna (train, test) como DataFrames."""
    # Remove Time, mantém V1-V28 + Amount + Class
    df = df.drop(columns=["Time"])

    X = df.drop(columns=["Class"])
    y = df["Class"]

    # Divisão estratificada: mantém proporção de fraudes em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,  # crítico para datasets desbalanceados
    )

    # Escala apenas Amount — V1-V28 já estão normalizadas via PCA
    pipeline = build_pipeline()
    X_train = X_train.copy()
    X_test = X_test.copy()
    X_train["Amount"] = pipeline.fit_transform(X_train[["Amount"]])
    X_test["Amount"] = pipeline.transform(X_test[["Amount"]])

    train = pd.concat([X_train, y_train], axis=1)
    test = pd.concat([X_test, y_test], axis=1)

    print(f"\nTreino : {train.shape[0]:,} amostras")
    print(f"Teste  : {test.shape[0]:,} amostras")

    return train, test


def save(train: pd.DataFrame, test: pd.DataFrame) -> tuple[Path, Path]:
    """Salva os datasets processados em Parquet."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    train_path = PROCESSED_DIR / "train.parquet"
    test_path = PROCESSED_DIR / "test.parquet"
    train.to_parquet(train_path, index=False)
    test.to_parquet(test_path, index=False)
    print(f"\nSalvo: {train_path}")
    print(f"Salvo: {test_path}")
    return train_path, test_path


# ── Orquestração com MLflow ───────────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print("Pipeline de Feature Engineering")
    print("=" * 50)

    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name="feature-engineering-v1"):
        # 1. Carrega dados
        df = load_raw(RAW_FILE)

        # 2. Loga estatísticas do dataset bruto
        stats = report_class_balance(df)
        mlflow.log_params({
            "raw_shape_rows": df.shape[0],
            "raw_shape_cols": df.shape[1],
            "test_size": TEST_SIZE,
            "random_state": RANDOM_STATE,
        })
        mlflow.log_metrics(stats)

        # 3. Aplica feature engineering
        train, test = engineer_features(df)

        # 4. Salva em Parquet
        train_path, test_path = save(train, test)

        # 5. Loga artefatos no MLflow (MinIO)
        mlflow.log_artifact(str(train_path), artifact_path="processed")
        mlflow.log_artifact(str(test_path), artifact_path="processed")

        mlflow.log_params({
            "train_samples": len(train),
            "test_samples": len(test),
            "features": list(train.drop(columns=["Class"]).columns),
        })

        run_id = mlflow.active_run().info.run_id  # type: ignore[union-attr]
        print(f"\nMLflow run_id : {run_id}")
        print(f"Experimento   : {EXPERIMENT_NAME}")
        print("\nAcesse: http://localhost:5000")

    print("\nFeature engineering concluído.")


if __name__ == "__main__":
    main()
