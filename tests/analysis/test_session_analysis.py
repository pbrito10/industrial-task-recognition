from pathlib import Path

import pandas as pd
import pytest

from analysis import session_analysis

_ORDER = ["Porca", "Montagem", "Saida"]


def _write_debug_csv(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "debug_test.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def _row(
    timestamp: str,
    event_type: str,
    zone: str,
    duration_s: float,
    cycle_number: int = 1,
) -> dict:
    return {
        "timestamp_iso": timestamp,
        "event_type": event_type,
        "zone": zone,
        "duration_s": duration_s,
        "cycle_number": cycle_number,
    }


@pytest.fixture(autouse=True)
def expected_order(monkeypatch):
    monkeypatch.setattr(session_analysis, "_load_expected_order", lambda: _ORDER)


def test_build_table_marks_timeout_recovered_as_correct(tmp_path):
    csv_path = _write_debug_csv(tmp_path, [
        _row("2024-01-01T10:00:01.000", "TASK_COMPLETE", "Porca", 2.0),
        _row("2024-01-01T10:00:02.000", "TASK_TIMEOUT", "Montagem", 30.0),
        _row("2024-01-01T10:00:03.000", "TASK_COMPLETE", "Montagem", 4.0),
        _row("2024-01-01T10:00:04.000", "TASK_COMPLETE", "Saida", 1.5),
    ])

    table = session_analysis.build_table(csv_path)

    assert table.loc[1, "Porca"] == "2.0s"
    assert table.loc[1, "Montagem"] == "TIMEOUT→OK 4.0s"
    assert table.loc[1, "Saida"] == "1.5s"
    assert table.loc[1, "Ordem correta"] == "Sim"
    assert table.loc[1, "Estado"] == "Correto"
    assert table.loc[1, "Duração total (s)"] == pytest.approx(7.5)


def test_build_table_marks_timeout_without_recovery_as_anomaly(tmp_path):
    csv_path = _write_debug_csv(tmp_path, [
        _row("2024-01-01T10:00:01.000", "TASK_COMPLETE", "Porca", 2.0),
        _row("2024-01-01T10:00:02.000", "TASK_TIMEOUT", "Montagem", 30.0),
        _row("2024-01-01T10:00:03.000", "TASK_COMPLETE", "Saida", 1.5),
    ])

    table = session_analysis.build_table(csv_path)

    assert table.loc[1, "Montagem"] == "TIMEOUT"
    assert table.loc[1, "Ordem correta"] == "Não"
    assert table.loc[1, "Estado"] == "Anomalia"


def test_repeated_zones_get_numbered_columns():
    cols = session_analysis._col_names(["Montagem", "Porca", "Montagem"])

    assert cols == ["Montagem_1", "Porca", "Montagem_2"]
