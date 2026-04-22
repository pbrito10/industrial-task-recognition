"""
Testa a lógica pura de calibração de perspetiva sem necessitar de câmara.
cv2.getPerspectiveTransform e cv2.warpPerspective são testados com valores reais
porque são operações matriciais determinísticas — não precisam de mock.
"""
from __future__ import annotations

import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from calibration.calibrate_perspective import (
    PerspectiveCalibrator,
    PerspectiveResult,
    _compute_output_height,
    _load_undistort_maps,
)


# --- PerspectiveCalibrator ---

class TestPerspectiveCalibrator:

    @pytest.fixture
    def calibrator(self):
        return PerspectiveCalibrator(output_size=(800, 565))

    def test_initial_point_count_zero(self, calibrator):
        assert calibrator.point_count == 0

    def test_not_complete_initially(self, calibrator):
        assert not calibrator.is_complete

    def test_add_point(self, calibrator):
        calibrator.add_point(10, 20)
        assert calibrator.point_count == 1
        assert calibrator.points == [(10, 20)]

    def test_add_4_points_is_complete(self, calibrator):
        for i in range(4):
            calibrator.add_point(i * 10, i * 10)
        assert calibrator.is_complete

    def test_add_beyond_4_ignored(self, calibrator):
        for i in range(6):
            calibrator.add_point(i, i)
        assert calibrator.point_count == 4

    def test_reset_clears_points(self, calibrator):
        calibrator.add_point(1, 2)
        calibrator.reset()
        assert calibrator.point_count == 0
        assert not calibrator.is_complete

    def test_compute_raises_if_incomplete(self, calibrator):
        calibrator.add_point(0, 0)
        with pytest.raises(ValueError):
            calibrator.compute()

    def test_compute_returns_result(self, calibrator):
        # Quadrado 100x100 → mapeado para retângulo de saída
        for x, y in [(0, 0), (100, 0), (100, 100), (0, 100)]:
            calibrator.add_point(x, y)
        result = calibrator.compute()
        assert isinstance(result, PerspectiveResult)
        assert result.output_size == (800, 565)

    def test_compute_matrix_is_3x3(self, calibrator):
        for x, y in [(0, 0), (100, 0), (100, 100), (0, 100)]:
            calibrator.add_point(x, y)
        result = calibrator.compute()
        assert result.matrix.shape == (3, 3)


# --- PerspectiveResult ---

class TestPerspectiveResult:

    def _make_result(self, output_size=(800, 565)) -> PerspectiveResult:
        src = np.float32([[0, 0], [100, 0], [100, 100], [0, 100]])
        import cv2
        dst = np.float32([
            [0,                     0],
            [output_size[0] - 1,    0],
            [output_size[0] - 1,    output_size[1] - 1],
            [0,                     output_size[1] - 1],
        ])
        M = cv2.getPerspectiveTransform(src, dst)
        return PerspectiveResult(matrix=M, output_size=output_size)

    def test_apply_returns_correct_size(self):
        result = self._make_result(output_size=(400, 300))
        frame  = np.zeros((200, 200, 3), dtype=np.uint8)
        warped = result.apply(frame)
        assert warped.shape[1] == 400  # width
        assert warped.shape[0] == 300  # height

    def test_save_creates_npz(self, tmp_path):
        path = tmp_path / "perspective.npz"
        self._make_result().save(path)
        assert path.exists()

    def test_saved_npz_contains_keys(self, tmp_path):
        path = tmp_path / "perspective.npz"
        self._make_result().save(path)
        data = np.load(str(path))
        assert "M" in data
        assert "output_size" in data

    def test_saved_matrix_round_trip(self, tmp_path):
        path = tmp_path / "perspective.npz"
        result = self._make_result()
        result.save(path)
        data = np.load(str(path))
        np.testing.assert_array_almost_equal(data["M"], result.matrix)

    def test_saved_output_size_round_trip(self, tmp_path):
        path = tmp_path / "perspective.npz"
        result = self._make_result(output_size=(640, 480))
        result.save(path)
        data = np.load(str(path))
        assert tuple(data["output_size"].tolist()) == (640, 480)


# --- _compute_output_height ---

def test_compute_output_height_a4_proportions():
    # A4: 297x210 mm, saída: 800px de largura
    # altura = int(800 * 210/297) = 565
    height = _compute_output_height()
    assert height == 565


# --- _load_undistort_maps ---

class TestLoadUndistortMaps:

    def test_returns_none_if_no_path(self):
        assert _load_undistort_maps(None, 640, 480) is None

    def test_returns_none_if_file_missing(self, tmp_path):
        result = _load_undistort_maps(str(tmp_path / "nao_existe.npz"), 640, 480)
        assert result is None

    def test_loads_maps_from_valid_npz(self, tmp_path):
        # Grava um ficheiro de calibração mínimo válido
        path = tmp_path / "lens.npz"
        K    = np.eye(3, dtype=np.float64) * 500
        K[0, 2] = 320
        K[1, 2] = 240
        dist = np.zeros((1, 5), dtype=np.float64)
        np.savez(str(path), K=K, dist=dist, newcameramtx=K)

        maps = _load_undistort_maps(str(path), 640, 480)
        assert maps is not None
        map1, map2 = maps
        assert map1.shape == (480, 640)
        assert map2.shape == (480, 640)

    def test_loads_maps_without_newcameramtx_key(self, tmp_path):
        # Ficheiros antigos sem newcameramtx fazem fallback para K
        path = tmp_path / "lens_old.npz"
        K    = np.eye(3, dtype=np.float64) * 500
        K[0, 2] = 320
        K[1, 2] = 240
        dist = np.zeros((1, 5), dtype=np.float64)
        np.savez(str(path), K=K, dist=dist)  # sem newcameramtx

        maps = _load_undistort_maps(str(path), 640, 480)
        assert maps is not None
