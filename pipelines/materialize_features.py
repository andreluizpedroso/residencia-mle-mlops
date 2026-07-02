"""
Prepara e materializa features no Feature Store (Feast).

Fluxo:
    1. Lê o CSV bruto e adiciona colunas de entidade e timestamp
    2. Salva em data/feast/transactions.parquet (fonte offline do Feast)
    3. Aplica definições de features (equivale a 'feast apply')
    4. Materializa para a online store (equivale a 'feast materialize')

Uso:
    uv run python pipelines/materialize_features.py
"""

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))  # garante que feature_store/ é importável

load_dotenv(ROOT / ".env")
os.environ.setdefault("PYTHONUTF8", "1")

import pandas as pd
from feast import FeatureStore

from feature_store.features import transaction, transaction_features

# ── Configuração ──────────────────────────────────────────────────────────────

RAW_FILE = Path(__file__).parent.parent / "data" / "raw" / "creditcard.csv"
FEAST_DATA_DIR = Path(__file__).parent.parent / "data" / "feast"
FEATURE_STORE_DIR = Path(__file__).parent.parent / "feature_store"


# ── Funções ───────────────────────────────────────────────────────────────────

def prepare_feast_data(raw_path: Path, output_dir: Path) -> Path:
    """Transforma o CSV bruto em formato compatível com Feast.

    Feast exige uma coluna de entidade (transaction_id) e uma de
    timestamp (event_timestamp) em cada linha do parquet.
    """
    df = pd.read_csv(raw_path).drop(columns=["Time"])

    n = len(df)
    df["transaction_id"] = range(n)

    # Simula 1 ano de transações com timestamps retroativos
    now = datetime.now(tz=UTC)
    step = timedelta(seconds=int(365 * 24 * 3600 / n))
    start = now - timedelta(days=365)
    df["event_timestamp"] = [start + step * i for i in range(n)]

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "transactions.parquet"
    df.to_parquet(output_path, index=False)

    print(f"Dados preparados: {n:,} transacoes -> {output_path}")
    return output_path


def apply_and_materialize(feature_store_dir: Path) -> None:
    """Registra as features e sincroniza offline → online store."""
    store = FeatureStore(repo_path=str(feature_store_dir))

    store.apply([transaction, transaction_features])
    print("Definições de features aplicadas.")

    end = datetime.now(tz=UTC)
    start = end - timedelta(days=366)
    store.materialize(start_date=start, end_date=end)
    print("Features materializadas para o online store.")


# ── Orquestração ──────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print("Feature Store — Feast")
    print("=" * 50)

    print("\n[1/2] Preparando dados...")
    prepare_feast_data(RAW_FILE, FEAST_DATA_DIR)

    print("\n[2/2] Aplicando e materializando features...")
    apply_and_materialize(FEATURE_STORE_DIR)

    print("\nFeature Store pronto.")
    print(f"Registry  : {FEAST_DATA_DIR / 'registry.db'}")
    print(f"Online DB : {FEAST_DATA_DIR / 'online_store.db'}")


if __name__ == "__main__":
    main()
