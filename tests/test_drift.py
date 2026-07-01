"""Testes para o pipeline de detecção de drift."""

from pathlib import Path

import numpy as np
import pandas as pd


def _make_df(n: int = 200, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    data: dict[str, np.ndarray] = {f"V{i}": rng.normal(size=n) for i in range(1, 29)}
    data["Amount"] = rng.exponential(scale=100, size=n)
    return pd.DataFrame(data)


def test_simulate_current_data_shape() -> None:
    from pipelines.detect_drift import simulate_current_data

    reference = _make_df(500)
    current = simulate_current_data(reference, n=100)
    assert current.shape == (100, reference.shape[1])


def test_simulate_current_data_introduces_drift() -> None:
    from pipelines.detect_drift import simulate_current_data

    reference = _make_df(500)
    current = simulate_current_data(reference, n=300)
    # Amount com drift intencional (loc=1.5) — média deve ser significativamente maior
    assert current["Amount"].mean() > reference["Amount"].mean() * 1.2


def test_run_drift_report_returns_expected_keys(tmp_path: Path) -> None:
    from pipelines.detect_drift import run_drift_report

    reference = _make_df(300)
    current = _make_df(100, seed=99)
    summary = run_drift_report(reference, current, reports_dir=tmp_path)

    assert "share_drifted_features" in summary
    assert "number_drifted_features" in summary
    assert "dataset_drift_detected" in summary
    assert 0.0 <= summary["share_drifted_features"] <= 1.0
    assert (tmp_path / "drift_report.html").exists()
    assert (tmp_path / "drift_report.json").exists()
