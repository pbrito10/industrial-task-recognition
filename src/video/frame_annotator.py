"""Funções de desenho sobre frames OpenCV (esqueleto, ROIs, FPS).

Todas as funções recebem um frame BGR e desenham diretamente nele (in-place).
Não guardam estado — podem ser chamadas em qualquer ordem e a qualquer momento.
"""
from __future__ import annotations

import cv2
import numpy as np

from src.detection.hand_detection import HandDetection
from src.roi.region_of_interest import RegionOfInterest
from src.roi.roi_collection import RoiCollection
from src.shared.hand_side import HandSide

# ── Constantes visuais ───────────────────────────────────────────────────────

_FONT = cv2.FONT_HERSHEY_SIMPLEX
_LINE_THICKNESS = 2
_KEYPOINT_RADIUS = 4
_FILL_ALPHA = 0.2

# Ligações entre landmarks que formam o esqueleto da mão (convenção MediaPipe)
_HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Polegar
    (0, 5), (5, 6), (6, 7), (7, 8),        # Indicador
    (0, 9), (9, 10), (10, 11), (11, 12),   # Médio
    (0, 13), (13, 14), (14, 15), (15, 16), # Anelar
    (0, 17), (17, 18), (18, 19), (19, 20), # Mindinho
    (5, 9), (9, 13), (13, 17),             # Palma
]

# Cores por lado da mão (BGR)
_HAND_COLORS: dict[HandSide, tuple[int, int, int]] = {
    HandSide.LEFT: (255, 100, 0),
    HandSide.RIGHT: (0, 200, 50),
}

# Cores fixas por nome de zona (BGR)
_ZONE_COLOR_DEFAULT  = (50, 205, 50)    # verde — zonas de recolha de peças
_ZONE_COLOR_ASSEMBLY = (0, 165, 255)    # laranja — zona de montagem
_ZONE_COLOR_EXIT     = (255, 100, 0)    # azul — zona de saída

_ZONE_COLOR_MAP: dict[str, tuple[int, int, int]] = {
    "Zona de Montagem": _ZONE_COLOR_ASSEMBLY,
    "Zona de Saida":    _ZONE_COLOR_EXIT,
}


# ── Funções auxiliares (privadas) ────────────────────────────────────────────

def zone_color(name: str) -> tuple[int, int, int]:
    """Devolve a cor BGR associada ao nome da zona.

    Zonas especiais (montagem, saída) têm cor própria.
    Todas as outras zonas de recolha são verdes.
    """
    return _ZONE_COLOR_MAP.get(name, _ZONE_COLOR_DEFAULT)


# ── Funções de desenho (privadas) ────────────────────────────────────────────

def _draw_skeleton(frame: np.ndarray, keypoints, color: tuple[int, int, int]) -> None:
    """Traça as linhas de ligação entre landmarks que formam o esqueleto."""
    for start_idx, end_idx in _HAND_CONNECTIONS:
        start = keypoints.by_index(start_idx).position
        end   = keypoints.by_index(end_idx).position
        cv2.line(frame, (start.x, start.y), (end.x, end.y), color, _LINE_THICKNESS)


def _draw_keypoints(frame: np.ndarray, keypoints, color: tuple[int, int, int]) -> None:
    """Desenha um círculo em cada landmark."""
    for kp in keypoints.all():
        cv2.circle(frame, (kp.position.x, kp.position.y), _KEYPOINT_RADIUS, color, -1)


def _draw_bounding_box(
    frame: np.ndarray,
    detection: HandDetection,
    color: tuple[int, int, int],
) -> None:
    """Desenha o retângulo e o label com lado e confiança.

    O lado exibido é o invertido da deteção porque a câmara está em espelho.
    """
    tl = detection.bounding_box.top_left
    br = detection.bounding_box.bottom_right
    cv2.rectangle(frame, (tl.x, tl.y), (br.x, br.y), color, _LINE_THICKNESS)

    flipped_side = HandSide.RIGHT if detection.hand_side == HandSide.LEFT else HandSide.LEFT
    label = f"{flipped_side.value}  {detection.confidence.as_percentage():.0f}%"
    cv2.putText(frame, label, (tl.x, tl.y - 8), _FONT, 0.5, color, 1)


# ── API pública ──────────────────────────────────────────────────────────────

def draw_hand(frame: np.ndarray, detection: HandDetection) -> None:
    """Desenha esqueleto, keypoints e bounding box de uma mão."""
    color = _HAND_COLORS[detection.hand_side]
    _draw_skeleton(frame, detection.keypoints, color)
    _draw_keypoints(frame, detection.keypoints, color)
    _draw_bounding_box(frame, detection, color)


def draw_detections(frame: np.ndarray, detections: list[HandDetection]) -> None:
    """Desenha todas as deteções de mãos no frame."""
    for detection in detections:
        draw_hand(frame, detection)


def draw_roi(
    frame: np.ndarray,
    roi: RegionOfInterest,
    color: tuple[int, int, int],
    *,
    selected: bool = False,
) -> None:
    """Desenha uma ROI com preenchimento semi-transparente, contorno e label.

    Se `selected=True`, o contorno é mais espesso para indicar zona ativa.
    """
    tl = (roi.top_left.x, roi.top_left.y)
    br = (roi.bottom_right.x, roi.bottom_right.y)

    # Preenchimento semi-transparente
    overlay = frame.copy()
    cv2.rectangle(overlay, tl, br, color, -1)
    cv2.addWeighted(overlay, _FILL_ALPHA, frame, 1 - _FILL_ALPHA, 0, frame)

    # Contorno (mais espesso se selecionada)
    cv2.rectangle(frame, tl, br, color, 2 if not selected else 3)

    cv2.putText(frame, roi.name, (tl[0] + 5, tl[1] + 20), _FONT, 0.6, color, 2)


def draw_rois(
    frame: np.ndarray,
    rois: RoiCollection,
    *,
    selected_name: str | None = None,
) -> None:
    """Desenha todas as ROIs da coleção.

    Args:
        selected_name: Nome da ROI ativa (contorno mais espesso).
    """
    for roi in rois.all():
        color = zone_color(roi.name)
        draw_roi(frame, roi, color, selected=roi.name == selected_name)


def draw_fps(frame: np.ndarray, fps: float) -> None:
    """Mostra FPS e resolução no canto superior esquerdo."""
    h, w = frame.shape[:2]
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25), _FONT, 0.6, (255, 255, 255), 1)
    cv2.putText(frame, f"{w}x{h}", (10, 50), _FONT, 0.6, (255, 255, 255), 1)
