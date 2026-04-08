"""Renderiza o frame de guia para o projetor.

Fundo preto (projetor desligado = bancada sem luz extra).
A zona atual é destacada com rectângulo pulsante; uma seta pulsante aponta
do centro da zona atual para o centro da zona seguinte.
"""
from __future__ import annotations

import math
import time
from typing import Optional

import cv2
import numpy as np

from src.projection.homography import transform_roi
from src.roi.roi_collection import RoiCollection

# Zona atual — verde visível em bancada branca
_COLOR_BGR    = (0, 220, 0)
_BORDER_THICK = 8
# Seta para a zona seguinte — branco para contrastar com o verde
_ARROW_COLOR_BGR = (255, 255, 255)
_ARROW_THICK     = 6
_ARROW_TIP_FRAC  = 0.05   # comprimento da ponta como fracção do comprimento total

_PULSE_HZ  = 1.5   # frequência de pulsação (Hz)
_FILL_MIN  = 0.15  # alpha mínimo do fill
_FILL_MAX  = 0.40  # alpha máximo do fill

_FONT       = cv2.FONT_HERSHEY_SIMPLEX
_FONT_SCALE = 1.8
_FONT_THICK = 3


class ProjectorRenderer:
    """Gera frames 1920×1080 com a zona atual destacada e seta para a seguinte."""

    def __init__(
        self,
        width:  int,
        height: int,
        rois:   RoiCollection,
        H:      np.ndarray,
    ) -> None:
        self._width  = width
        self._height = height
        self._rois   = rois
        self._H      = H

    def render(
        self,
        current_zone: Optional[str],
        next_zone:    Optional[str],
    ) -> np.ndarray:
        """Gera um frame com a zona atual destacada e seta para a seguinte.

        Se current_zone for None ou não existir nos ROIs, devolve frame preto.
        A seta só é desenhada se next_zone existir e for diferente de current_zone.
        """
        frame = np.zeros((self._height, self._width, 3), dtype=np.uint8)

        if current_zone is None:
            return frame

        tl, br = self._zone_bounds(current_zone)
        if tl is None:
            return frame

        alpha = self._pulse_alpha()

        # --- overlay: fill da zona atual + seta (ambos pulsam juntos) ---
        overlay = frame.copy()
        cv2.rectangle(overlay, tl, br, _COLOR_BGR, -1)

        current_center = self._center(tl, br)
        next_center    = self._zone_center(next_zone, exclude=current_zone)
        if next_center is not None:
            cv2.arrowedLine(
                overlay, current_center, next_center,
                _ARROW_COLOR_BGR, _ARROW_THICK,
                tipLength=_ARROW_TIP_FRAC,
            )

        cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)

        # --- elementos sólidos por cima do blend ---
        cv2.rectangle(frame, tl, br, _COLOR_BGR, _BORDER_THICK)
        self._draw_label(frame, current_zone, tl, br)

        return frame

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _pulse_alpha(self) -> float:
        return _FILL_MIN + (_FILL_MAX - _FILL_MIN) * (
            0.5 + 0.5 * math.sin(time.time() * 2 * math.pi * _PULSE_HZ)
        )

    def _zone_bounds(
        self, zone: str
    ) -> tuple[tuple[int, int], tuple[int, int]] | tuple[None, None]:
        """Devolve (tl, br) clipados em píxeis do projetor, ou (None, None)."""
        roi = self._rois.get(zone)
        if roi is None:
            return None, None

        tl, br = transform_roi(roi, self._H)
        tl = (max(0, tl[0]), max(0, tl[1]))
        br = (min(self._width - 1, br[0]), min(self._height - 1, br[1]))

        if tl[0] >= br[0] or tl[1] >= br[1]:
            return None, None

        return tl, br

    def _center(
        self, tl: tuple[int, int], br: tuple[int, int]
    ) -> tuple[int, int]:
        return ((tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2)

    def _zone_center(
        self, zone: Optional[str], exclude: Optional[str]
    ) -> Optional[tuple[int, int]]:
        """Centro da zona em coordenadas do projetor, ou None se indisponível."""
        if zone is None or zone == exclude:
            return None
        tl, br = self._zone_bounds(zone)
        if tl is None:
            return None
        return self._center(tl, br)

    def _draw_label(
        self,
        frame: np.ndarray,
        text:  str,
        tl:    tuple[int, int],
        br:    tuple[int, int],
    ) -> None:
        """Nome da zona centrado dentro do retângulo."""
        (tw, th), _ = cv2.getTextSize(text, _FONT, _FONT_SCALE, _FONT_THICK)
        cx  = (tl[0] + br[0]) // 2
        cy  = (tl[1] + br[1]) // 2
        org = (cx - tw // 2, cy + th // 2)
        cv2.putText(frame, text, org, _FONT, _FONT_SCALE, _COLOR_BGR, _FONT_THICK)
