import json

from src.output.session_config_snapshot import (
    expected_order_from_snapshot,
    snapshot_path_for_csv,
    write_session_config_snapshot,
)
from src.roi.roi_collection import RoiCollection
from tests.conftest import make_roi


def _config() -> dict:
    return {
        "tracking": {
            "zones": ["A", "B", "C"],
            "two_hands_zones": ["B"],
            "cycle_zone_order": ["A", "B", "C"],
            "exit_zone": "C",
            "dwell_time_seconds": 0.5,
            "task_timeout_seconds": 30.0,
            "stillness_threshold_px": 5.0,
            "detection_gap_threshold_s": 1.0,
        }
    }


def test_snapshot_path_is_derived_from_csv_name(tmp_path):
    csv_path = tmp_path / "debug_2026-04-27_14h48.csv"

    assert snapshot_path_for_csv(csv_path) == tmp_path / "debug_2026-04-27_14h48_config.json"


def test_write_snapshot_saves_config_and_rois(tmp_path):
    csv_path = tmp_path / "debug_session.csv"
    rois = RoiCollection()
    rois.add(make_roi("A", 1, 2, 3, 4))

    path = write_session_config_snapshot(csv_path, _config(), rois)

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["source_csv"] == "debug_session.csv"
    assert data["config"]["tracking"]["cycle_zone_order"] == ["A", "B", "C"]
    assert data["rois"] == [{"name": "A", "x1": 1, "y1": 2, "x2": 3, "y2": 4}]


def test_expected_order_from_snapshot_reads_historical_order(tmp_path):
    csv_path = tmp_path / "debug_session.csv"

    write_session_config_snapshot(csv_path, _config(), RoiCollection())

    assert expected_order_from_snapshot(csv_path) == ["A", "B", "C"]
