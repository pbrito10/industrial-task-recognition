"""
Testa a lógica pura de calibração de lente sem necessitar de câmara.
cv2.calibrateCamera é mockado — testamos a construção de pontos,
acumulação de capturas, guards de validação e persistência.
"""
from __future__ import annotations

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from calibration.calibrate_lens import LensCalibrator, CalibrationResult


# --- LensCalibrator ---

class TestLensCalibrator:

    def test_build_object_points_shape(self):
        cal = LensCalibrator(checkerboard_size=(6, 4), square_size_mm=35.0)
        # 6*4 = 24 pontos, cada um com 3 coords
        pts = cal._obj_pts_template
        assert pts.shape == (24, 3)

    def test_build_object_points_z_zero(self):
        cal = LensCalibrator(checkerboard_size=(6, 4), square_size_mm=35.0)
        assert np.all(cal._obj_pts_template[:, 2] == 0)

    def test_build_object_points_spacing(self):
        cal = LensCalibrator(checkerboard_size=(3, 2), square_size_mm=10.0)
        pts = cal._obj_pts_template
        # Primeiro ponto: (0,0,0); segundo: (10,0,0); quarto: (0,10,0)
        assert pts[0, 0] == pytest.approx(0.0)
        assert pts[1, 0] == pytest.approx(10.0)

    def test_initial_capture_count_is_zero(self):
        cal = LensCalibrator((6, 4), 35.0)
        assert cal.capture_count == 0

    def test_capture_increments_count(self):
        cal = LensCalibrator((6, 4), 35.0)
        fake_corners = np.zeros((24, 1, 2), dtype=np.float32)
        cal.add(fake_corners)
        assert cal.capture_count == 1

    def test_calibrate_raises_if_no_detections(self):
        cal = LensCalibrator((6, 4), 35.0)
        with pytest.raises(ValueError):
            cal.calibrate((640, 480))

    @patch("calibration.calibrate_lens.cv2.calibrateCamera")
    @patch("calibration.calibrate_lens.cv2.getOptimalNewCameraMatrix")
    @patch("calibration.calibrate_lens.cv2.projectPoints")
    @patch("calibration.calibrate_lens.cv2.norm")
    def test_calibrate_returns_result(
        self, mock_norm, mock_proj, mock_optimal, mock_calib
    ):
        K    = np.eye(3, dtype=np.float64)
        dist = np.zeros((1, 5), dtype=np.float64)
        mock_calib.return_value   = (0.5, K, dist, [np.zeros((3,1))]*15, [np.zeros((3,1))]*15)
        mock_optimal.return_value = (K, (0, 0, 640, 480))
        mock_proj.return_value    = (np.zeros((24, 1, 2)), None)
        mock_norm.return_value    = 0.3

        cal = LensCalibrator((6, 4), 35.0)
        corners = np.zeros((24, 1, 2), dtype=np.float32)
        for _ in range(15):
            cal.add(corners)

        result = cal.calibrate((640, 480))
        assert isinstance(result, CalibrationResult)
        assert result.rms == pytest.approx(0.5)


# --- CalibrationResult.save / load ---

class TestCalibrationResultPersistence:

    def _make_result(self) -> CalibrationResult:
        K    = np.eye(3, dtype=np.float64) * 500
        dist = np.array([[0.1, -0.2, 0.0, 0.0, 0.05]])
        newK = np.eye(3, dtype=np.float64) * 490
        return CalibrationResult(
            camera_matrix=K,
            dist_coeffs=dist,
            rms=0.45,
            new_camera_matrix=newK,
            roi=(0, 0, 640, 480),
            per_image_errors=[0.4, 0.5],
        )

    def test_save_creates_npz(self, tmp_path):
        path = tmp_path / "data" / "lens_calibration.npz"
        result = self._make_result()
        result.save(path)
        assert path.exists()

    def test_saved_npz_contains_keys(self, tmp_path):
        path = tmp_path / "lens.npz"
        self._make_result().save(path)
        data = np.load(str(path))
        assert "K" in data
        assert "dist" in data
        assert "newcameramtx" in data
        assert "roi" in data

    def test_saved_values_round_trip(self, tmp_path):
        path = tmp_path / "lens.npz"
        result = self._make_result()
        result.save(path)
        data = np.load(str(path))
        np.testing.assert_array_almost_equal(data["K"], result.camera_matrix)
        np.testing.assert_array_almost_equal(data["dist"], result.dist_coeffs)
