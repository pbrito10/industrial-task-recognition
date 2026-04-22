"""
Testa a lógica de conversão do MediapipeDetector sem carregar o modelo.
O HandLandmarker é mockado — testamos os métodos de transformação de coordenadas
e a integração com HandDetection, que são independentes do modelo.
"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.detection.mediapipe_detector import MediapipeDetector
from src.shared.hand_side import HandSide
from src.shared.point import Point


def _make_landmark(x: float, y: float, z: float = 0.0):
    return SimpleNamespace(x=x, y=y, z=z)


def _make_handedness(name: str = "Right", score: float = 0.95):
    category = SimpleNamespace(category_name=name, score=score)
    return [category]


def _make_result(landmarks_list, handedness_list):
    result = MagicMock()
    result.hand_landmarks = landmarks_list
    result.handedness     = handedness_list
    return result


@pytest.fixture
def detector():
    """Cria um MediapipeDetector com o HandLandmarker mockado."""
    with patch("src.detection.mediapipe_detector.mp_vision.HandLandmarker.create_from_options") as mock_create:
        mock_create.return_value = MagicMock()
        det = MediapipeDetector(model_path="fake_path.task")
    return det


# --- _to_pixel_point ---

def test_to_pixel_point_center():
    lm    = _make_landmark(0.5, 0.5)
    point = MediapipeDetector._to_pixel_point(lm, width=640, height=480)
    assert point == Point(320, 240)


def test_to_pixel_point_origin():
    lm    = _make_landmark(0.0, 0.0)
    point = MediapipeDetector._to_pixel_point(lm, width=640, height=480)
    assert point == Point(0, 0)


def test_to_pixel_point_bottom_right():
    lm    = _make_landmark(1.0, 1.0)
    point = MediapipeDetector._to_pixel_point(lm, width=640, height=480)
    assert point == Point(640, 480)


def test_to_pixel_point_fractional():
    lm    = _make_landmark(0.25, 0.75)
    point = MediapipeDetector._to_pixel_point(lm, width=800, height=600)
    assert point == Point(200, 450)


# --- _clamp_range ---

def test_clamp_range_normal():
    min_v, max_v = MediapipeDetector._clamp_range([50, 100, 150], 200)
    assert min_v == 40   # 50 - 10 (margem)
    assert max_v == 160  # 150 + 10


def test_clamp_range_at_lower_boundary():
    min_v, _ = MediapipeDetector._clamp_range([0, 100], 200)
    assert min_v == 0  # não vai abaixo de 0


def test_clamp_range_at_upper_boundary():
    _, max_v = MediapipeDetector._clamp_range([100, 195], 200)
    assert max_v == 199  # não ultrapassa frame_max - 1


# --- detect (com mock do landmarker) ---

def test_detect_returns_empty_when_no_hands(detector):
    detector._landmarker.detect_for_video.return_value = _make_result([], [])
    frame  = np.zeros((480, 640, 3), dtype=np.uint8)
    result = detector.detect(frame)
    assert result == []


def test_detect_returns_one_detection_per_hand(detector):
    # 21 landmarks normalizados em (0.5, 0.5)
    landmarks = [_make_landmark(0.5, 0.5) for _ in range(21)]
    mock_result = _make_result(
        landmarks_list=[landmarks],
        handedness_list=[_make_handedness("Right", 0.97)],
    )
    detector._landmarker.detect_for_video.return_value = mock_result
    frame    = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detector.detect(frame)
    assert len(detections) == 1


def test_detect_hand_side_right(detector):
    landmarks   = [_make_landmark(0.5, 0.5) for _ in range(21)]
    mock_result = _make_result([landmarks], [_make_handedness("Right", 0.9)])
    detector._landmarker.detect_for_video.return_value = mock_result
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    det   = detector.detect(frame)[0]
    assert det.hand_side == HandSide.RIGHT


def test_detect_hand_side_left(detector):
    landmarks   = [_make_landmark(0.5, 0.5) for _ in range(21)]
    mock_result = _make_result([landmarks], [_make_handedness("Left", 0.9)])
    detector._landmarker.detect_for_video.return_value = mock_result
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    det   = detector.detect(frame)[0]
    assert det.hand_side == HandSide.LEFT


def test_detect_landmark_coordinates_converted(detector):
    # Landmark 0 (pulso) em (0.5, 0.5) → pixel (320, 240) num frame 640x480
    landmarks   = [_make_landmark(0.5, 0.5) for _ in range(21)]
    mock_result = _make_result([landmarks], [_make_handedness()])
    detector._landmarker.detect_for_video.return_value = mock_result
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    det   = detector.detect(frame)[0]
    assert det.keypoints.wrist().position == Point(320, 240)


def test_detect_confidence_from_handedness(detector):
    landmarks   = [_make_landmark(0.5, 0.5) for _ in range(21)]
    mock_result = _make_result([landmarks], [_make_handedness(score=0.92)])
    detector._landmarker.detect_for_video.return_value = mock_result
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    det   = detector.detect(frame)[0]
    assert det.confidence.value == pytest.approx(0.92, abs=0.001)


def test_detect_two_hands(detector):
    lm1 = [_make_landmark(0.25, 0.25) for _ in range(21)]
    lm2 = [_make_landmark(0.75, 0.75) for _ in range(21)]
    mock_result = _make_result(
        [lm1, lm2],
        [_make_handedness("Right"), _make_handedness("Left")],
    )
    detector._landmarker.detect_for_video.return_value = mock_result
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    dets  = detector.detect(frame)
    assert len(dets) == 2
    sides = {d.hand_side for d in dets}
    assert sides == {HandSide.RIGHT, HandSide.LEFT}


def test_release_closes_landmarker(detector):
    detector.release()
    detector._landmarker.close.assert_called_once()
