from __future__ import annotations

from typing import Any, TypedDict, cast


class CameraConfig(TypedDict):
    index: int
    width: int
    height: int
    flip: bool
    calibration_path: str
    perspective_path: str


class CalibrationConfig(TypedDict):
    checkerboard_size: list[int]
    square_size_mm: float
    min_captures: int


class DetectionConfig(TypedDict):
    model_path: str
    max_num_hands: int
    min_detection_confidence: float
    min_tracking_confidence: float


class TrackingConfig(TypedDict):
    dwell_time_seconds: float
    task_timeout_seconds: float
    stillness_threshold_px: float
    zones: list[str]
    two_hands_zones: list[str]
    cycle_zone_order: list[str]
    exit_zone: str
    detection_gap_threshold_s: float


class DashboardConfig(TypedDict):
    data_path: str
    refresh_seconds: float


class OutputConfig(TypedDict):
    excel_output_dir: str
    sessions_subdir: str
    record_video: bool
    video_fps: float


class AppConfig(TypedDict):
    camera: CameraConfig
    calibration: CalibrationConfig
    detection: DetectionConfig
    tracking: TrackingConfig
    dashboard: DashboardConfig
    output: OutputConfig


def validate_config(raw: Any) -> AppConfig:
    """Valida a forma do settings.yaml no arranque."""
    if not isinstance(raw, dict):
        raise ValueError("settings.yaml deve conter um mapa no topo.")

    _require_mapping(raw, "camera")
    _require_mapping(raw, "calibration")
    _require_mapping(raw, "detection")
    _require_mapping(raw, "tracking")
    _require_mapping(raw, "dashboard")
    _require_mapping(raw, "output")

    camera = raw["camera"]
    _require_type(camera, "index", int)
    _require_type(camera, "width", int)
    _require_type(camera, "height", int)
    _require_type(camera, "flip", bool)
    _require_type(camera, "calibration_path", str)
    _require_type(camera, "perspective_path", str)

    calibration = raw["calibration"]
    _require_list(calibration, "checkerboard_size", int)
    _require_number(calibration, "square_size_mm")
    _require_type(calibration, "min_captures", int)

    detection = raw["detection"]
    _require_type(detection, "model_path", str)
    _require_type(detection, "max_num_hands", int)
    _require_number(detection, "min_detection_confidence")
    _require_number(detection, "min_tracking_confidence")

    tracking = raw["tracking"]
    _require_number(tracking, "dwell_time_seconds")
    _require_number(tracking, "task_timeout_seconds")
    _require_number(tracking, "stillness_threshold_px")
    _require_list(tracking, "zones", str)
    _require_list(tracking, "two_hands_zones", str)
    _require_list(tracking, "cycle_zone_order", str)
    _require_type(tracking, "exit_zone", str)
    _require_number(tracking, "detection_gap_threshold_s")

    dashboard = raw["dashboard"]
    _require_type(dashboard, "data_path", str)
    _require_number(dashboard, "refresh_seconds")

    output = raw["output"]
    _require_type(output, "excel_output_dir", str)
    _require_type(output, "sessions_subdir", str)
    _require_type(output, "record_video", bool)
    _require_number(output, "video_fps")

    return cast(AppConfig, raw)


def _require_mapping(config: dict, key: str) -> None:
    if key not in config or not isinstance(config[key], dict):
        raise ValueError(f"Config inválida: '{key}' deve existir e ser um mapa.")


def _require_type(config: dict, key: str, expected: type) -> None:
    if key not in config or not isinstance(config[key], expected):
        raise ValueError(f"Config inválida: '{key}' deve ser {expected.__name__}.")


def _require_number(config: dict, key: str) -> None:
    if key not in config or isinstance(config[key], bool) or not isinstance(config[key], (int, float)):
        raise ValueError(f"Config inválida: '{key}' deve ser numérico.")


def _require_list(config: dict, key: str, item_type: type) -> None:
    if key not in config or not isinstance(config[key], list):
        raise ValueError(f"Config inválida: '{key}' deve ser uma lista.")
    if not all(isinstance(item, item_type) for item in config[key]):
        raise ValueError(f"Config inválida: todos os valores de '{key}' devem ser {item_type.__name__}.")
