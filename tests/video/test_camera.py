from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch, call

import numpy as np
import pytest

from src.video.camera import Camera


def _make_mock_cap(frame: np.ndarray | None = None, succeed: bool = True):
    """Cria um mock de cv2.VideoCapture que devolve o frame dado."""
    if frame is None:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock = MagicMock()
    mock.isOpened.return_value = True
    mock.read.return_value     = (succeed, frame)
    mock.get.return_value      = 30.0
    return mock


def _lens_npz(tmp_path: Path) -> Path:
    """Grava um .npz de calibração de lente mínimo e válido."""
    path = tmp_path / "lens.npz"
    K    = np.eye(3, dtype=np.float64) * 500
    K[0, 2] = 320; K[1, 2] = 240
    dist = np.zeros((1, 5), dtype=np.float64)
    np.savez(str(path), K=K, dist=dist, newcameramtx=K)
    return path


def _perspective_npz(tmp_path: Path) -> Path:
    """Grava um .npz de perspetiva mínimo e válido."""
    import cv2
    path = tmp_path / "perspective.npz"
    src  = np.float32([[0,0],[100,0],[100,100],[0,100]])
    dst  = np.float32([[0,0],[639,0],[639,479],[0,479]])
    M    = cv2.getPerspectiveTransform(src, dst)
    np.savez(str(path), M=M, output_size=np.array([640, 480]))
    return path


# --- read_frame básico ---

@patch("src.video.camera.cv2.VideoCapture")
def test_read_frame_returns_frame(mock_cap_cls):
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_cap_cls.return_value = _make_mock_cap(frame)
    cam   = Camera(0, 640, 480)
    result = cam.read_frame()
    assert result is not None
    assert result.shape == (480, 640, 3)


@patch("src.video.camera.cv2.VideoCapture")
def test_read_frame_returns_none_on_failure(mock_cap_cls):
    mock_cap_cls.return_value = _make_mock_cap(succeed=False)
    cam = Camera(0, 640, 480)
    assert cam.read_frame() is None


# --- flip ---

@patch("src.video.camera.cv2.VideoCapture")
def test_flip_rotates_frame_180(mock_cap_cls):
    # Frame assimétrico: canto superior-esquerdo branco, resto preto
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    frame[0, 0] = [255, 255, 255]

    mock_cap_cls.return_value = _make_mock_cap(frame.copy())
    cam = Camera(0, 4, 4, flip=True)
    result = cam.read_frame()

    # Após flip 180°, o pixel branco deve estar no canto inferior-direito
    assert result[3, 3, 0] == 255
    assert result[0, 0, 0] == 0


@patch("src.video.camera.cv2.VideoCapture")
def test_no_flip_leaves_frame_unchanged(mock_cap_cls):
    frame = np.zeros((4, 4, 3), dtype=np.uint8)
    frame[0, 0] = [255, 0, 0]

    mock_cap_cls.return_value = _make_mock_cap(frame.copy())
    cam    = Camera(0, 4, 4, flip=False)
    result = cam.read_frame()
    assert result[0, 0, 0] == 255


# --- calibração de lente ---

@patch("src.video.camera.cv2.VideoCapture")
def test_calibration_path_loads_undistort_maps(mock_cap_cls, tmp_path):
    lens_path = _lens_npz(tmp_path)
    mock_cap_cls.return_value = _make_mock_cap()
    cam = Camera(0, 640, 480, calibration_path=str(lens_path))
    assert cam._undistort_maps is not None


@patch("src.video.camera.cv2.VideoCapture")
def test_missing_calibration_path_skips_undistort(mock_cap_cls, tmp_path):
    mock_cap_cls.return_value = _make_mock_cap()
    cam = Camera(0, 640, 480, calibration_path=str(tmp_path / "nao_existe.npz"))
    assert cam._undistort_maps is None


@patch("src.video.camera.cv2.VideoCapture")
def test_none_calibration_path_skips_undistort(mock_cap_cls):
    mock_cap_cls.return_value = _make_mock_cap()
    cam = Camera(0, 640, 480, calibration_path=None)
    assert cam._undistort_maps is None


# --- calibração de perspetiva ---

@patch("src.video.camera.cv2.VideoCapture")
def test_perspective_path_loads_matrix(mock_cap_cls, tmp_path):
    persp_path = _perspective_npz(tmp_path)
    mock_cap_cls.return_value = _make_mock_cap()
    cam = Camera(0, 640, 480, perspective_path=str(persp_path))
    assert cam._perspective_M is not None
    assert cam._perspective_size == (640, 480)


@patch("src.video.camera.cv2.VideoCapture")
def test_perspective_applied_changes_frame_size(mock_cap_cls, tmp_path):
    import cv2
    src  = np.float32([[0,0],[100,0],[100,100],[0,100]])
    dst  = np.float32([[0,0],[799,0],[799,564],[0,564]])
    M    = cv2.getPerspectiveTransform(src, dst)
    path = tmp_path / "persp.npz"
    np.savez(str(path), M=M, output_size=np.array([800, 565]))

    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_cap_cls.return_value = _make_mock_cap(frame)
    cam    = Camera(0, 640, 480, perspective_path=str(path))
    result = cam.read_frame()
    assert result.shape == (565, 800, 3)


# --- from_config ---

@patch("src.video.camera.cv2.VideoCapture")
def test_from_config_creates_camera(mock_cap_cls):
    mock_cap_cls.return_value = _make_mock_cap()
    config = {"index": 0, "width": 640, "height": 480, "flip": False}
    cam = Camera.from_config(config)
    assert cam._flip is False


# --- fps / is_open / release ---

@patch("src.video.camera.cv2.VideoCapture")
def test_fps(mock_cap_cls):
    mock_cap_cls.return_value = _make_mock_cap()
    cam = Camera(0, 640, 480)
    assert cam.fps() == 30.0


@patch("src.video.camera.cv2.VideoCapture")
def test_is_open(mock_cap_cls):
    mock_cap_cls.return_value = _make_mock_cap()
    assert Camera(0, 640, 480).is_open() is True


@patch("src.video.camera.cv2.VideoCapture")
def test_release_calls_capture_release(mock_cap_cls):
    mock = _make_mock_cap()
    mock_cap_cls.return_value = mock
    Camera(0, 640, 480).release()
    mock.release.assert_called_once()
