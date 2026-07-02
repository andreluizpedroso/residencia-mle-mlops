"""
DAG de retreino automático: detecta drift e retreina o modelo se necessário.

Fluxo:
    detect_drift → [drift?] → retrain_model → register_model → fim
                            → [sem drift]  → skip → fim

Schedule: semanal (toda segunda-feira às 02:00 UTC)
"""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import BranchPythonOperator, PythonOperator

from airflow import DAG

PROJECT_DIR = "/opt/airflow/project"
DRIFT_THRESHOLD = 0.1  # retreina se > 10% das features driftaram

default_args = {
    "owner": "mlops",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "email_on_failure": False,
}


def _detect_drift(**context: object) -> dict[str, object]:
    """Roda detecção de drift e publica resultado no XCom."""
    import sys

    sys.path.insert(0, PROJECT_DIR)

    from pathlib import Path

    from pipelines.detect_drift import (
        load_reference,
        run_drift_report,
        simulate_current_data,
    )

    reference = load_reference(Path(PROJECT_DIR) / "data" / "raw" / "creditcard.csv")
    current = simulate_current_data(reference)
    summary = run_drift_report(
        reference,
        current,
        reports_dir=Path(PROJECT_DIR) / "data" / "reports",
    )

    context["ti"].xcom_push(key="drift_summary", value=summary)  # type: ignore[index]
    return summary


def _branch_on_drift(**context: object) -> str:
    """Decide se retreina com base no share de features driftadas."""
    summary = context["ti"].xcom_pull(task_ids="detect_drift", key="drift_summary")  # type: ignore[index]
    share = float(summary["share_drifted_features"])
    return "retrain_model" if share > DRIFT_THRESHOLD else "skip_retraining"


with DAG(
    dag_id="fraud_retraining",
    description="Detecta drift semanal e retreina o modelo de fraude se necessario",
    schedule="0 2 * * 1",  # toda segunda às 02:00 UTC
    start_date=datetime(2025, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["mlops", "fraud", "retraining"],
) as dag:

    detect_drift = PythonOperator(
        task_id="detect_drift",
        python_callable=_detect_drift,
    )

    branch = BranchPythonOperator(
        task_id="should_retrain",
        python_callable=_branch_on_drift,
    )

    retrain_model = BashOperator(
        task_id="retrain_model",
        bash_command=f"cd {PROJECT_DIR} && python pipelines/train.py",
    )

    register_model = BashOperator(
        task_id="register_model",
        bash_command=f"cd {PROJECT_DIR} && python pipelines/register_model.py",
    )

    skip_retraining = EmptyOperator(task_id="skip_retraining")

    done = EmptyOperator(
        task_id="done",
        trigger_rule="none_failed_min_one_success",
    )

    detect_drift >> branch >> [retrain_model, skip_retraining]
    retrain_model >> register_model >> done
    skip_retraining >> done
