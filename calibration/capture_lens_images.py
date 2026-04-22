"""
Captura imagens do checkerboard para calibração de lente.

Como usar:
  1. Imprime um tabuleiro de xadrez com CHECKERBOARD_SIZE cantos internos.
  2. Executa: python calibration/capture_lens_images.py
  3. Mostra o tabuleiro à câmara em várias posições e ângulos variados.
  4. Pressiona SPACE quando os cantos estiverem a verde para guardar a imagem.
  5. ESC para terminar.

As imagens ficam em calibration/data/lens_images/.
Depois corre calibrate_lens.py para calcular a calibração.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import cv2
import numpy as np
import yaml

if not os.environ.get("DISPLAY"):
    os.environ["DISPLAY"] = ":0"

_SETTINGS_PATH = Path(__file__).parent.parent / "config" / "settings.yaml"
CAMERA_INDEX: int = 0
OUTPUT_DIR: Path = Path(__file__).parent / "data" / "lens_images"

_SUBPIX_CRITERIA = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)


def _draw_hud(frame: np.ndarray, count: int, detected: bool) -> None:
    h = frame.shape[0]
    color  = (0, 200, 0) if detected else (0, 0, 200)
    status = "DETETADO — SPACE para guardar" if detected else "A procurar checkerboard..."
    cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, f"Guardadas: {count}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, "SPACE: guardar  ESC: sair", (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)


def main() -> None:
    with open(_SETTINGS_PATH) as f:
        settings = yaml.safe_load(f)
    checkerboard_size: tuple[int, int] = tuple(settings["calibration"]["checkerboard_size"])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Erro: não foi possível abrir a câmara {CAMERA_INDEX}.")
        sys.exit(1)

    # Conta imagens já existentes para não sobrescrever
    existing = sorted(OUTPUT_DIR.glob("*.jpg"))
    count = len(existing)

    cv2.namedWindow("Captura de Imagens", cv2.WINDOW_NORMAL)
    print("=== Captura de Imagens para Calibração de Lente ===")
    print(f"Checkerboard: {checkerboard_size[0]}x{checkerboard_size[1]} cantos internos")
    print(f"A guardar em: {OUTPUT_DIR}")
    print(f"Imagens já existentes: {count}\n")
    print("Mostra o tabuleiro em posições e ângulos variados.")
    print("SPACE quando os cantos estiverem verdes | ESC para sair\n")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Erro a ler frame.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        found, corners = cv2.findChessboardCorners(gray, checkerboard_size, None)

        display = frame.copy()
        if found:
            corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), _SUBPIX_CRITERIA)
            cv2.drawChessboardCorners(display, checkerboard_size, corners, found)

        _draw_hud(display, count, found)
        cv2.imshow("Captura de Imagens", display)

        key = cv2.waitKey(1) & 0xFF

        if key == 27:  # ESC
            print(f"\nTerminado. {count} imagens guardadas em {OUTPUT_DIR}")
            break

        if key == ord(' ') and found:
            path = OUTPUT_DIR / f"frame_{count:03d}.jpg"
            cv2.imwrite(str(path), frame)
            count += 1
            print(f"Guardada: {path.name}  (total: {count})")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
