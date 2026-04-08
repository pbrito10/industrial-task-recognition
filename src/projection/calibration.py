"""Calibração câmara → projetor com um único marcador ArUco.

Um marcador ArUco tem 4 cantos em posições conhecidas no projetor.
A câmara deteta esses mesmos 4 cantos no espaço da câmara.
4 pares de pontos são suficientes para cv2.findHomography.

Fluxo:
  1. Projeta um marcador ArUco grande centrado na bancada.
  2. Câmara captura os 4 cantos do marcador.
  3. cv2.findHomography(camera_corners, projector_corners) → H.
  4. H é guardado via homography.save().
"""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from src.projection.homography import save as save_homography

_DICT_ID     = cv2.aruco.DICT_4X4_50
_MARKER_ID   = 0
_MARKER_SIZE = 600   # píxeis do projetor — grande para deteção fiável


def _marker_corners_projector(width: int, height: int) -> np.ndarray:
    """4 cantos do marcador no espaço do projetor (ordem ArUco: TL, TR, BR, BL)."""
    cx   = width  // 2
    cy   = height // 2
    half = _MARKER_SIZE // 2
    return np.array([
        [cx - half, cy - half],   # top-left
        [cx + half, cy - half],   # top-right
        [cx + half, cy + half],   # bottom-right
        [cx - half, cy + half],   # bottom-left
    ], dtype=np.float64)


def _generate_marker(size: int) -> np.ndarray:
    """Gera imagem do marcador ArUco em escala de cinzentos."""
    dictionary = cv2.aruco.getPredefinedDictionary(_DICT_ID)
    return cv2.aruco.generateImageMarker(dictionary, _MARKER_ID, size)


def _detect_marker_corners(frame_bgr: np.ndarray) -> np.ndarray | None:
    """Deteta o marcador e devolve os 4 cantos em coordenadas da câmara, ou None."""
    dictionary = cv2.aruco.getPredefinedDictionary(_DICT_ID)
    detector   = cv2.aruco.ArucoDetector(dictionary, cv2.aruco.DetectorParameters())
    corners, ids, _ = detector.detectMarkers(frame_bgr)

    if ids is None:
        return None

    for i, marker_id in enumerate(ids.flatten()):
        if marker_id == _MARKER_ID:
            # corners[i] tem shape (1, 4, 2) — remove a dimensão exterior
            return corners[i][0].astype(np.float64)

    return None


def run_calibration(
    camera_index:          int,
    camera_width:          int,
    camera_height:         int,
    projector_width:       int,
    projector_height:      int,
    display_offset_x:      int,
    display_offset_y:      int,
    calibration_path:      Path,
    stabilization_seconds: int = 5,
) -> bool:
    """Corre a calibração ArUco de marcador único. Devolve True se bem sucedido."""
    import tkinter as tk
    from PIL import Image, ImageTk

    proj_corners = _marker_corners_projector(projector_width, projector_height)
    cx = projector_width  // 2
    cy = projector_height // 2
    half = _MARKER_SIZE // 2

    # --- Projeta o marcador centrado via tkinter ---
    root = tk.Tk()
    root.wm_attributes('-type', 'splash')
    root.geometry(f"{projector_width}x{projector_height}+{display_offset_x}+{display_offset_y}")
    root.configure(bg="black")

    canvas = tk.Canvas(root, width=projector_width, height=projector_height,
                       bg="black", highlightthickness=0)
    canvas.pack()

    img_gray = _generate_marker(_MARKER_SIZE)
    photo    = ImageTk.PhotoImage(Image.fromarray(img_gray))
    canvas.create_image(cx - half, cy - half, anchor="nw", image=photo)

    # Câmara aberta antes da projeção para estar pronta durante a captura
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)

    root.update()
    print(f"  Marcador ArUco projetado ao centro. "
          f"A aguardar estabilização ({stabilization_seconds}s)...")

    end = time.time() + stabilization_seconds
    while time.time() < end:
        root.update()
        time.sleep(0.05)

    # --- Captura com o marcador ainda projetado ---
    cam_corners = None
    for _ in range(15):
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue
        cam_corners = _detect_marker_corners(frame)
        if cam_corners is not None:
            break
        time.sleep(0.15)

    cap.release()
    root.destroy()

    if cam_corners is None:
        print(
            "  Erro: marcador ArUco não detetado na câmara.\n"
            "  Verifica se o projetor está ligado e o marcador está numa zona plana."
        )
        return False

    # --- Calcula H a partir dos 4 cantos ---
    H, mask = cv2.findHomography(cam_corners, proj_corners)

    if H is None:
        print("  Erro: não foi possível calcular a homografia.")
        return False

    save_homography(calibration_path, H)
    print("  Calibração ArUco concluída. Homografia guardada.")
    return True
