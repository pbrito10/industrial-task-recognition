"""Calibração automática câmara → projetor.

Fluxo:
  1. Projeta 4 círculos verde-brilhante em posições conhecidas no projetor.
  2. Câmara captura o frame e deteta os círculos por cor (HSV).
  3. cv2.findHomography(camera_pts, projector_pts) → H.
  4. H é guardado via homography.save().

Usa círculos coloridos (verde) em vez de brancos porque a bancada é branca
— deteção por matiz HSV é robusta independentemente do fundo.
"""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from src.projection.homography import save as save_homography

# Margem relativa para os círculos de calibração (10% de cada lado)
_MARGIN = 0.10
# Raio do círculo projetado (em píxeis do projetor)
_CIRCLE_RADIUS = 35
# Cor do círculo: verde puro (BGR)
_CIRCLE_COLOR_BGR = (0, 255, 0)
# Intervalo HSV para detetar verde brilhante projetado numa superfície branca
_HSV_LOW  = np.array([40,  80, 80],  dtype=np.uint8)
_HSV_HIGH = np.array([80, 255, 255], dtype=np.uint8)


def _circle_positions(width: int, height: int) -> list[tuple[int, int]]:
    """4 posições de calibração: cantos com margem de 10%."""
    mx = int(width  * _MARGIN)
    my = int(height * _MARGIN)
    return [
        (mx,          my),
        (width - mx,  my),
        (mx,          height - my),
        (width - mx,  height - my),
    ]


def _sort_four_points(pts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Ordena 4 pontos: top-left, top-right, bottom-left, bottom-right."""
    by_y   = sorted(pts, key=lambda p: p[1])
    top    = sorted(by_y[:2], key=lambda p: p[0])
    bottom = sorted(by_y[2:], key=lambda p: p[0])
    return [top[0], top[1], bottom[0], bottom[1]]


def _build_projector_frame(width: int, height: int) -> np.ndarray:
    """Frame preto com 4 círculos verdes nos cantos."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    for pt in _circle_positions(width, height):
        cv2.circle(frame, pt, _CIRCLE_RADIUS, _CIRCLE_COLOR_BGR, -1)
    return frame


def _detect_green_circles(
    frame_bgr: np.ndarray,
    expected: int,
) -> list[tuple[float, float]] | None:
    """Deteta círculos verdes no frame por segmentação HSV.

    Devolve lista de centroides ou None se não encontrou o número esperado.
    """
    hsv  = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, _HSV_LOW, _HSV_HIGH)

    # Remove ruído com morfologia
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
    mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    n_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)

    # Filtra componentes por área mínima (ignora label 0 = fundo)
    min_area = 150
    blobs = [
        (centroids[i][0], centroids[i][1])
        for i in range(1, n_labels)
        if stats[i, cv2.CC_STAT_AREA] >= min_area
    ]

    if len(blobs) != expected:
        return None

    return blobs


def run_calibration(
    camera_index:             int,
    camera_width:             int,
    camera_height:            int,
    projector_width:          int,
    projector_height:         int,
    display_offset_x:         int,
    display_offset_y:         int,
    calibration_path:         Path,
    stabilization_seconds:    int = 5,
) -> bool:
    """Corre a calibração automática. Devolve True se bem sucedido."""

    proj_pts = _circle_positions(projector_width, projector_height)

    # --- Projeta o padrão de calibração ---
    # Ordem obrigatória: imshow primeiro (cria a janela), depois move e fullscreen.
    # O event loop do OpenCV depende de waitKey para renderizar — time.sleep sozinho
    # congela a janela antes de aparecer no projetor.
    # WINDOW_FULLSCREEN é ignorado por muitos window managers Linux quando a janela
    # está noutro monitor. Usa-se WINDOW_NORMAL + moveWindow + resizeWindow, que
    # funciona independentemente do compositor.
    win = "Calibracao_Projetor"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.imshow(win, _build_projector_frame(projector_width, projector_height))
    cv2.waitKey(200)
    cv2.moveWindow(win, display_offset_x, display_offset_y)
    cv2.waitKey(200)
    cv2.resizeWindow(win, projector_width, projector_height)
    print(f"  [debug] janela em ({display_offset_x}, {display_offset_y}), {projector_width}×{projector_height}")

    # Mantém o event loop vivo durante a estabilização (waitKey em vez de sleep)
    n_ticks = stabilization_seconds * 5  # 200 ms por tick
    print(f"  Padrão de calibração projetado. A aguardar estabilização ({stabilization_seconds}s)...")
    for _ in range(n_ticks):
        cv2.waitKey(200)

    # --- Captura e deteta ---
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)

    camera_blobs = None
    for attempt in range(15):
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue
        camera_blobs = _detect_green_circles(frame, len(proj_pts))
        if camera_blobs is not None:
            break
        time.sleep(0.15)

    cap.release()
    cv2.destroyWindow(win)

    if camera_blobs is None:
        print(
            "  Erro: não foram detetados os 4 marcadores verdes na câmara.\n"
            "  Verifica se o projetor está ligado e alinhado com a bancada."
        )
        return False

    # --- Ordena os pontos e calcula H ---
    proj_sorted   = _sort_four_points([(float(x), float(y)) for x, y in proj_pts])
    camera_sorted = _sort_four_points(camera_blobs)

    H, mask = cv2.findHomography(
        np.array(camera_sorted,  dtype=np.float64),
        np.array(proj_sorted,    dtype=np.float64),
    )

    if H is None:
        print("  Erro: não foi possível calcular a homografia.")
        return False

    inliers = int(mask.sum()) if mask is not None else 0
    if inliers < 3:
        print(f"  Aviso: homografia com poucos inliers ({inliers}/4). Repete a calibração.")
        return False

    save_homography(calibration_path, H)
    print(f"  Calibração concluída ({inliers}/4 inliers). Homografia guardada.")
    return True
