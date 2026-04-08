"""Calibração câmara → projetor com marcadores ArUco.

Fluxo:
  1. Projeta 4 marcadores ArUco (IDs 0–3) em posições conhecidas no projetor.
  2. Câmara captura o frame e deteta os marcadores.
  3. Cada ID mapeia diretamente para a posição projetada — sem ordenação.
  4. cv2.findHomography(camera_pts, projector_pts) → H.
  5. H é guardado via homography.save().

ArUco é mais robusto que deteção por cor: funciona com iluminação variável,
bancadas de qualquer cor, e o ID único de cada marker elimina ambiguidade
na correspondência câmara ↔ projetor.
"""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from src.projection.homography import save as save_homography

_MARGIN      = 0.10          # margem relativa para os markers (10% de cada lado)
_MARKER_SIZE = 120           # tamanho do marker em píxeis do projetor
_DICT_ID     = cv2.aruco.DICT_4X4_50

# IDs e respetivas posições: 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right
_MARKER_IDS = [0, 1, 2, 3]


def _marker_centers(width: int, height: int) -> dict[int, tuple[int, int]]:
    """Centros dos 4 markers em píxeis do projetor, com margem de 10%."""
    mx = int(width  * _MARGIN)
    my = int(height * _MARGIN)
    return {
        0: (mx,          my),
        1: (width  - mx, my),
        2: (mx,          height - my),
        3: (width  - mx, height - my),
    }


def _generate_marker(marker_id: int, size: int) -> np.ndarray:
    """Gera imagem de um marcador ArUco em escala de cinzentos (size × size)."""
    dictionary = cv2.aruco.getPredefinedDictionary(_DICT_ID)
    return cv2.aruco.generateImageMarker(dictionary, marker_id, size)


def _detect_aruco_markers(
    frame_bgr:    np.ndarray,
    expected_ids: list[int],
) -> dict[int, tuple[float, float]] | None:
    """Deteta markers ArUco no frame.

    Devolve ID → centro (cx, cy) se todos os expected_ids foram encontrados,
    None caso contrário.
    """
    dictionary = cv2.aruco.getPredefinedDictionary(_DICT_ID)
    detector   = cv2.aruco.ArucoDetector(dictionary, cv2.aruco.DetectorParameters())
    corners, ids, _ = detector.detectMarkers(frame_bgr)

    if ids is None:
        return None

    found: dict[int, tuple[float, float]] = {}
    for i, marker_id in enumerate(ids.flatten()):
        if marker_id in expected_ids:
            # Centro = média dos 4 cantos do marker
            cx = float(corners[i][0][:, 0].mean())
            cy = float(corners[i][0][:, 1].mean())
            found[int(marker_id)] = (cx, cy)

    if not all(mid in found for mid in expected_ids):
        return None

    return found


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
    """Corre a calibração ArUco. Devolve True se bem sucedido."""
    import tkinter as tk
    from PIL import Image, ImageTk

    centers = _marker_centers(projector_width, projector_height)
    half    = _MARKER_SIZE // 2

    # --- Projeta os markers ArUco via tkinter ---
    root = tk.Tk()
    root.geometry(f"{projector_width}x{projector_height}+{display_offset_x}+{display_offset_y}")
    root.overrideredirect(True)
    root.configure(bg="black")

    canvas = tk.Canvas(root, width=projector_width, height=projector_height,
                       bg="black", highlightthickness=0)
    canvas.pack()

    # Guarda referências para evitar garbage collection dos PhotoImage
    photo_refs = []
    for marker_id, (cx, cy) in centers.items():
        img_gray = _generate_marker(marker_id, _MARKER_SIZE)
        photo    = ImageTk.PhotoImage(Image.fromarray(img_gray))
        photo_refs.append(photo)
        canvas.create_image(cx - half, cy - half, anchor="nw", image=photo)

    root.update()
    print(f"  Markers ArUco projetados. A aguardar estabilização ({stabilization_seconds}s)...")

    end = time.time() + stabilization_seconds
    while time.time() < end:
        root.update()
        time.sleep(0.05)

    root.destroy()

    # --- Captura e deteta ---
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)

    found = None
    for _ in range(15):
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue
        found = _detect_aruco_markers(frame, _MARKER_IDS)
        if found is not None:
            break
        time.sleep(0.15)

    cap.release()

    if found is None:
        print(
            "  Erro: não foram detetados os 4 markers ArUco na câmara.\n"
            "  Verifica se o projetor está ligado e alinhado com a bancada."
        )
        return False

    # --- Correspondência direta por ID → sem necessidade de ordenar ---
    camera_pts    = np.array([found[mid]    for mid in _MARKER_IDS], dtype=np.float64)
    projector_pts = np.array([centers[mid]  for mid in _MARKER_IDS], dtype=np.float64)

    H, mask = cv2.findHomography(camera_pts, projector_pts)

    if H is None:
        print("  Erro: não foi possível calcular a homografia.")
        return False

    inliers = int(mask.sum()) if mask is not None else 0
    if inliers < 3:
        print(f"  Aviso: homografia com poucos inliers ({inliers}/4). Repete a calibração.")
        return False

    save_homography(calibration_path, H)
    print(f"  Calibração ArUco concluída ({inliers}/4 inliers). Homografia guardada.")
    return True
