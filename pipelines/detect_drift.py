"""
Pipeline de detecção de drift: compara a distribuição dos dados de produção
com os dados de treino (referência) usando Evidently AI.

Em produção, 'current data' viria de logs da API ou de uma tabela de
transações recentes. Aqui, simulamos com ruído para fins didáticos.

Uso:
    uv run python pipelines/detect_drift.py
"""

import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
os.environ.setdefault("PYTHONUTF8", "1")

import numpy as np
import pandas as pd
from evidently.core.metric_types import CountValue
from evidently.core.report import Report
from evidently.presets import DataDriftPreset, DataSummaryPreset

# ── Configuração ──────────────────────────────────────────────────────────────

RAW_FILE = Path(__file__).parent.parent / "data" / "raw" / "creditcard.csv"
REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"
FEATURES = [f"V{i}" for i in range(1, 29)] + ["Amount"]


# ── Tipos ─────────────────────────────────────────────────────────────────────

class DriftSummary(TypedDict):
    share_drifted_features: float
    number_drifted_features: int
    dataset_drift_detected: bool
    html_report: str
    json_report: str


# ── Funções ───────────────────────────────────────────────────────────────────

def load_reference(path: Path, n_samples: int = 10_000) -> pd.DataFrame:
    """Amostra do dataset de treino — serve como baseline para comparação."""
    df = pd.read_csv(path, usecols=FEATURES)
    return df.sample(n=min(n_samples, len(df)), random_state=42)


def simulate_current_data(reference: pd.DataFrame, n: int = 2_000) -> pd.DataFrame:
    """
    Simula dados de produção com drift intencional em Amount e V1.

    Em um sistema real, isso seria substituído por:
        pd.read_parquet("data/production_logs/last_7_days.parquet")
    """
    rng = np.random.default_rng(seed=99)
    current = reference.sample(n=n, random_state=1).reset_index(drop=True).copy()
    # Drift intencional: Amount com média 50% maior, V1 deslocado
    current["Amount"] = current["Amount"] * rng.normal(loc=1.5, scale=0.3, size=n)
    current["V1"] = current["V1"] + rng.normal(loc=0.5, scale=0.2, size=n)
    return current


def run_drift_report(
    reference: pd.DataFrame,
    current: pd.DataFrame,
    reports_dir: Path | None = None,
) -> DriftSummary:
    """Gera e salva relatório de drift. Retorna métricas resumidas."""
    out_dir = reports_dir if reports_dir is not None else REPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    report = Report(metrics=[DataDriftPreset(), DataSummaryPreset()])
    snapshot = report.run(reference_data=reference, current_data=current)

    html_path = out_dir / "drift_report.html"
    json_path = out_dir / "drift_report.json"
    snapshot.save_html(str(html_path))
    snapshot.save_json(str(json_path))

    # CountValue contém count (n features com drift) e share (proporção)
    n_drifted = 0
    share_drifted = 0.0
    for result in snapshot.metric_results.values():
        if isinstance(result, CountValue):
            n_drifted = int(result.count.value)
            share_drifted = float(result.share.value)
            break

    return DriftSummary(
        share_drifted_features=share_drifted,
        number_drifted_features=n_drifted,
        dataset_drift_detected=share_drifted > 0.5,
        html_report=str(html_path),
        json_report=str(json_path),
    )


# ── Orquestração ──────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 50)
    print("Detecção de Drift — Fraud Detection")
    print("=" * 50)

    reference = load_reference(RAW_FILE)
    print(f"Referência (treino): {len(reference):,} amostras")

    current = simulate_current_data(reference)
    print(f"Produção (atual)   : {len(current):,} amostras")

    print("\nAnalisando drift...")
    summary = run_drift_report(reference, current)

    print(f"\nDrift detectado    : {summary['dataset_drift_detected']}")
    print(f"Features com drift : {summary['number_drifted_features']}")
    print(f"% features com drift: {summary['share_drifted_features']:.1%}")
    print(f"\nRelatório HTML: {summary['html_report']}")
    print("Abra no browser para visualização completa.")


if __name__ == "__main__":
    main()
