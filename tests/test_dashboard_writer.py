"""Testes para src/output/dashboard_writer.py"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from src.output.dashboard_writer import DashboardWriter
from src.metrics.metrics_calculator import MetricsCalculator

T0    = datetime(2026, 1, 1, 10, 0, 0)
ZONES = ["Porca", "Montagem"]


def _snapshot():
    return MetricsCalculator(T0, ZONES).snapshot()


# -- write --------------------------------------------------------------------

def test_write_cria_ficheiro(tmp_path):
    path = tmp_path / "metrics.json"
    writer = DashboardWriter(path)
    writer.write(_snapshot())
    assert path.exists()

def test_write_json_valido(tmp_path):
    path = tmp_path / "metrics.json"
    writer = DashboardWriter(path)
    writer.write(_snapshot())
    data = json.loads(path.read_text())
    assert "captured_at" in data
    assert "cycle_metrics" in data
    assert "task_metrics" in data

def test_write_cria_diretorios_em_falta(tmp_path):
    path = tmp_path / "sub" / "dir" / "metrics.json"
    writer = DashboardWriter(path)
    writer.write(_snapshot())
    assert path.exists()
