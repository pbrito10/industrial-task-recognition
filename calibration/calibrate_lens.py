"""
Calibração intrínseca da câmara usando imagens de um tabuleiro de xadrez.

Como usar:
  1. Corre capture_lens_images.py para capturar imagens do checkerboard.
  2. Revê as imagens em calibration/data/lens_images/ e apaga as más.
  3. Executa: python calibration/calibrate_lens.py
  4. Resultado guardado em calibration/data/lens_calibration.npz.

Uso posterior no pipeline:
  data = np.load("calibration/data/lens_calibration.npz")
  K, dist = data["K"], data["dist"]
  frame_corrigido = cv2.undistort(frame, K, dist)
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import yaml

_SETTINGS_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"
IMAGES_DIR: Path = Path(__file__).parent / "data" / "lens_images"
OUTPUT_PATH: Path = Path(__file__).parent / "data" / "lens_calibration.npz"

_SUBPIX_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)


class LensCalibrator:
    """Recolhe capturas de checkerboard e calcula os parâmetros intrínsecos da câmara.

    Separa a lógica de calibração da lógica de captura/UI.
    """

    def __init__(self, checkerboard_size: tuple[int, int], square_size_mm: float) -> None:
        self._checkerboard = checkerboard_size
        self._obj_pts_template = self._build_object_points(checkerboard_size, square_size_mm)
        self._obj_pts: list[np.ndarray] = []   # pontos 3D (um por captura)
        self._img_pts: list[np.ndarray] = []   # pontos 2D correspondentes

    @staticmethod
    def _build_object_points(size: tuple[int, int], square_mm: float) -> np.ndarray:
        """Cria o array de pontos 3D do checkerboard no referencial do mundo (z=0)."""
        cols, rows = size
        pts = np.zeros((rows * cols, 3), dtype=np.float32)
        pts[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
        pts *= square_mm
        return pts

    def detect(self, frame: np.ndarray) -> tuple[bool, np.ndarray | None]:
        """Deteta e refina os cantos do checkerboard num frame.

        :return: (detetado, cantos_refinados_ou_None)
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(gray, self._checkerboard, None)
        if found:
            corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), _SUBPIX_CRITERIA)
        return found, (corners if found else None)

    def add(self, corners: np.ndarray) -> int:
        """Acumula os cantos detetados. Devolve o total acumulado."""
        self._obj_pts.append(self._obj_pts_template)
        self._img_pts.append(corners)
        return len(self._obj_pts)

    @property
    def capture_count(self) -> int:
        return len(self._obj_pts)

    def calibrate(self, image_size: tuple[int, int]) -> CalibrationResult:
        """Executa cv2.calibrateCamera com todas as deteções acumuladas.

        :param image_size: (width, height) do frame em píxeis
        :raises ValueError: se não houver deteções acumuladas
        """
        if self.capture_count == 0:
            raise ValueError("Nenhuma deteção acumulada.")

        rms, K, dist, rvecs, tvecs = cv2.calibrateCamera(
            self._obj_pts,
            self._img_pts,
            image_size,
            None,
            None,
        )

        # Refina a matriz intrínseca com alpha=1 (retém todos os píxeis; sem crop)
        w, h = image_size
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(K, dist, (w, h), 1, (w, h))

        # Erro de reprojeção por imagem — quanto mais próximo de 0, melhor
        per_image_errors = []
        for i in range(len(self._obj_pts)):
            imgpoints2, _ = cv2.projectPoints(self._obj_pts[i], rvecs[i], tvecs[i], K, dist)
            error = cv2.norm(self._img_pts[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
            per_image_errors.append(error)

        return CalibrationResult(
            camera_matrix=K,
            dist_coeffs=dist,
            rms=rms,
            new_camera_matrix=newcameramtx,
            roi=roi,
            per_image_errors=per_image_errors,
        )


class CalibrationResult:
    """Encapsula os parâmetros intrínsecos, distorção, matriz refinada e erros de reprojeção."""

    def __init__(
        self,
        camera_matrix: np.ndarray,
        dist_coeffs: np.ndarray,
        rms: float,
        new_camera_matrix: np.ndarray,
        roi: tuple[int, int, int, int],
        per_image_errors: list[float],
    ) -> None:
        self.camera_matrix = camera_matrix      # K original: focal lengths + ponto principal
        self.dist_coeffs = dist_coeffs          # [k1, k2, p1, p2, k3]
        self.rms = rms                           # erro de reprojeção médio em píxeis
        self.new_camera_matrix = new_camera_matrix  # K refinado por getOptimalNewCameraMatrix
        self.roi = roi                           # (x, y, w, h) — região válida após undistortion
        self.per_image_errors = per_image_errors

    def save(self, path: Path) -> None:
        """Grava os parâmetros em .npz. Cria as pastas intermédias se necessário."""
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(
            str(path),
            K=self.camera_matrix,
            dist=self.dist_coeffs,
            newcameramtx=self.new_camera_matrix,
            roi=np.array(self.roi),
        )
        print(f"\nCalibração guardada em: {path}")
        print(f"Erro de reprojeção (RMS total): {self.rms:.4f} px")
        print("\nErro por imagem:")
        for i, err in enumerate(self.per_image_errors):
            print(f"  Imagem {i + 1:2d}: {err:.4f} px")
        # Valores > 1 px indicam que as imagens capturadas podem ter má qualidade
        if self.rms > 1.0:
            print("\nAVISO: RMS > 1 px — considera capturar mais imagens ou verificar o checkerboard.")


def main() -> None:
    with open(_SETTINGS_PATH) as f:
        settings = yaml.safe_load(f)
    cal_cfg = settings["calibration"]
    checkerboard_size: tuple[int, int] = tuple(cal_cfg["checkerboard_size"])
    square_size_mm: float = cal_cfg["square_size_mm"]
    min_captures: int = cal_cfg["min_captures"]

    images = sorted(IMAGES_DIR.glob("*.jpg")) + sorted(IMAGES_DIR.glob("*.png"))
    if not images:
        print(f"Erro: nenhuma imagem encontrada em {IMAGES_DIR}")
        print("Corre primeiro capture_lens_images.py para capturar imagens.")
        return

    print("=== Calibração de Lente ===")
    print(f"Checkerboard: {checkerboard_size[0]}x{checkerboard_size[1]} cantos internos")
    print(f"Quadrado: {square_size_mm} mm | Mínimo necessário: {min_captures} capturas")
    print(f"Imagens encontradas: {len(images)}\n")

    calibrator = LensCalibrator(checkerboard_size, square_size_mm)
    image_size: tuple[int, int] | None = None

    for path in images:
        frame = cv2.imread(str(path))
        if frame is None:
            print(f"  AVISO: não foi possível ler {path.name} — ignorada.")
            continue

        if image_size is None:
            h, w = frame.shape[:2]
            image_size = (w, h)

        found, corners = calibrator.detect(frame)
        if found and corners is not None:
            calibrator.add(corners)
            print(f"  OK  {path.name}")
        else:
            print(f"  --  {path.name}  (checkerboard não detetado)")

    print(f"\nCapturas válidas: {calibrator.capture_count}/{len(images)}")

    if calibrator.capture_count < min_captures:
        print(f"Erro: são necessárias pelo menos {min_captures} capturas válidas.")
        print("Captura mais imagens com capture_lens_images.py.")
        return

    print("\nA calcular calibração...")
    result = calibrator.calibrate(image_size)
    result.save(OUTPUT_PATH)


if __name__ == "__main__":
    main()
