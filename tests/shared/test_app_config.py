import pytest

from src.shared.app_config import validate_config


def _config():
    return {
        "camera": {
            "index": 0,
            "width": 640,
            "height": 480,
            "flip": True,
            "calibration_path": "",
            "perspective_path": "",
        },
        "calibration": {
            "checkerboard_size": [6, 4],
            "square_size_mm": 35.0,
            "min_captures": 15,
        },
        "detection": {
            "model_path": "model/hand_landmarker.task",
            "max_num_hands": 2,
            "min_detection_confidence": 0.7,
            "min_tracking_confidence": 0.7,
        },
        "tracking": {
            "dwell_time_seconds": 0.5,
            "task_timeout_seconds": 30.0,
            "stillness_threshold_px": 5.0,
            "zones": ["Porca", "Montagem", "Saida"],
            "two_hands_zones": ["Montagem"],
            "cycle_zone_order": ["Porca", "Montagem", "Saida"],
            "exit_zone": "Saida",
            "detection_gap_threshold_s": 1.0,
        },
        "dashboard": {
            "data_path": "dashboard/data/metrics.json",
            "refresh_seconds": 1,
        },
        "output": {
            "excel_output_dir": "output/",
            "sessions_subdir": "sessions",
            "record_video": True,
            "video_fps": 10.0,
        },
    }


def test_validate_config_accepts_valid_settings():
    assert validate_config(_config())["tracking"]["exit_zone"] == "Saida"


def test_validate_config_rejects_missing_section():
    config = _config()
    del config["tracking"]

    with pytest.raises(ValueError):
        validate_config(config)


def test_validate_config_rejects_wrong_type():
    config = _config()
    config["tracking"]["zones"] = "Porca"

    with pytest.raises(ValueError):
        validate_config(config)
