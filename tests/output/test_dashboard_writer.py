import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from src.metrics.cycle_metrics import CycleMetrics
from src.metrics.task_metrics import TaskMetrics
from src.output.dashboard_writer import DashboardWriter
from src.output.metrics_snapshot import MetricsSnapshot


def _snapshot(task_metrics=None, cycle_metrics=None) -> MetricsSnapshot:
    if task_metrics is None:
        task_metrics = {}
    if cycle_metrics is None:
        cycle_metrics = CycleMetrics()
    return MetricsSnapshot(
        task_metrics=task_metrics,
        cycle_metrics=cycle_metrics,
        productive_time=timedelta(seconds=60),
        transition_time=timedelta(seconds=20),
        interruption_time=timedelta(seconds=10),
        productive_percentage=66.7,
        transition_percentage=22.2,
        interruption_percentage=11.1,
        bottleneck_zone=None,
        session_duration=timedelta(seconds=90),
        captured_at=datetime(2024, 1, 1, 12, 0, 0),
    )


def test_write_creates_file(tmp_path):
    writer = DashboardWriter(tmp_path / "data" / "metrics.json")
    writer.write(_snapshot())
    assert (tmp_path / "data" / "metrics.json").exists()


def test_write_produces_valid_json(tmp_path):
    path = tmp_path / "metrics.json"
    writer = DashboardWriter(path)
    writer.write(_snapshot())
    data = json.loads(path.read_text())
    assert isinstance(data, dict)


def test_time_breakdown_in_output(tmp_path):
    path = tmp_path / "metrics.json"
    writer = DashboardWriter(path)
    writer.write(_snapshot())
    data = json.loads(path.read_text())
    assert "time_breakdown" in data
    tb = data["time_breakdown"]
    assert "productive_pct" in tb
    assert "transition_pct" in tb
    assert "interruption_pct" in tb


def test_task_metrics_serialized(tmp_path):
    tm = TaskMetrics()
    tm.add(timedelta(seconds=3))
    tm.add(timedelta(seconds=7))
    path = tmp_path / "metrics.json"
    writer = DashboardWriter(path)
    writer.write(_snapshot(task_metrics={"Porca": tm}))
    data = json.loads(path.read_text())
    assert "Porca" in data["task_metrics"]
    assert data["task_metrics"]["Porca"]["count"] == 2


def test_empty_task_metrics_omitted(tmp_path):
    tm = TaskMetrics()  # count == 0
    path = tmp_path / "metrics.json"
    writer = DashboardWriter(path)
    writer.write(_snapshot(task_metrics={"Porca": tm}))
    data = json.loads(path.read_text())
    assert "Porca" not in data["task_metrics"]


def test_cycle_metrics_empty(tmp_path):
    path = tmp_path / "metrics.json"
    writer = DashboardWriter(path)
    writer.write(_snapshot())
    data = json.loads(path.read_text())
    assert data["cycle_metrics"]["count"] == 0


def test_atomic_write_no_tmp_file_left(tmp_path):
    path = tmp_path / "metrics.json"
    writer = DashboardWriter(path)
    writer.write(_snapshot())
    assert not (tmp_path / "metrics.tmp").exists()


def test_cycle_metrics_with_data(tmp_path):
    path = tmp_path / "metrics.json"
    writer = DashboardWriter(path)
    cm = CycleMetrics()
    cm.add(timedelta(seconds=60), sequence_in_order=True)
    cm.add(timedelta(seconds=80), sequence_in_order=False)
    writer.write(_snapshot(cycle_metrics=cm))
    data = json.loads(path.read_text())
    cm_data = data["cycle_metrics"]
    assert cm_data["count"] == 2
    assert cm_data["count_in_order"] == 1
    assert cm_data["count_probably_complete"] == 1
    assert "min_s" in cm_data
    assert "avg_s" in cm_data


def test_bottleneck_zone_in_output(tmp_path):
    path = tmp_path / "metrics.json"
    writer = DashboardWriter(path)
    snap = _snapshot()
    # Cria snapshot com bottleneck manualmente
    snap_with_bottleneck = MetricsSnapshot(
        **{**snap.__dict__, "bottleneck_zone": "Montagem"}
    )
    writer.write(snap_with_bottleneck)
    data = json.loads(path.read_text())
    assert data["bottleneck_zone"] == "Montagem"
