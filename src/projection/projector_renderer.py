"""Renderiza o frame de guia para o projetor.

Fundo preto (projetor desligado = bancada sem luz extra).
A zona ativa é destacada com um retângulo pulsante: borda sólida + fill
semitransparente cuja intensidade varia sinusoidalmente.
"""
from __future__ import annotations

import math
import time
from typing import Optional

import cv2
import numpy as np

from src.projection.homography import transform_roi
from src.roi.roi_collection import RoiCollection

# Cor do highlight em BGR — verde visível em bancada branca
_COLOR_BGR    = (0, 220, 0)
_BORDER_THICK = 8
_PULSE_HZ     = 1.5   # frequência de pulsação
_FILL_MIN     = 0.15  # alpha mínimo do fill
_FILL_MAX     = 0.40  # alpha máximo do fill
_FONT         = cv2.FONT_HERSHEY_SIMPLEX
_FONT_SCALE   = 1.8
_FONT_THICK   = 3


class ProjectorRenderer:
    """Gera frames 1920×1080 com a zona ativa destacada para o projetor."""

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

    def render(self, active_zone: Optional[str]) -> np.ndarray:
        """Gera um frame preto com a zona ativa destacada.

        Se active_zone for None ou não existir nos ROIs, devolve frame preto.
        """
        frame = np.zeros((self._height, self._width, 3), dtype=np.uint8)

        if active_zone is None:
            return frame

        if active_zone != getattr(self, '_last_logged_zone', None):
            self._last_logged_zone = active_zone
            self._log_next = True

        roi = self._rois.get(active_zone)
        if roi is None:
            if getattr(self, '_log_next', False):
                print(f"[renderer] ROI '{active_zone}' não encontrado")
                self._log_next = False
            return frame

        tl, br = transform_roi(roi, self._H)

        if getattr(self, '_log_next', False):
            print(f"[renderer] '{active_zone}'"
                  f"  cam=({roi.top_left.x},{roi.top_left.y})-({roi.bottom_right.x},{roi.bottom_right.y})"
                  f"  →  proj tl={tl} br={br}  (projetor {self._width}x{self._height})")
            self._log_next = False

        # Clipa para não sair dos limites do projetor
        tl = (max(0, tl[0]), max(0, tl[1]))
        br = (min(self._width - 1, br[0]), min(self._height - 1, br[1]))

        if tl[0] >= br[0] or tl[1] >= br[1]:
            return frame

        self._draw_pulsing_rect(frame, tl, br)
        self._draw_label(frame, active_zone, tl, br)

        return frame

    # ------------------------------------------------------------------
    # Helpers de desenho
    # ------------------------------------------------------------------

    def _draw_pulsing_rect(
        self,
        frame: np.ndarray,
        tl:    tuple[int, int],
        br:    tuple[int, int],
    ) -> None:
        """Fill semitransparente com intensidade que pulsa no tempo."""
        alpha = _FILL_MIN + (_FILL_MAX - _FILL_MIN) * (
            0.5 + 0.5 * math.sin(time.time() * 2 * math.pi * _PULSE_HZ)
        )
        overlay = frame.copy()
        cv2.rectangle(overlay, tl, br, _COLOR_BGR, -1)
        cv2.addWeighted(overlay, alpha, frame, 1.0 - alpha, 0, frame)

        # Borda sólida por cima do blend
        cv2.rectangle(frame, tl, br, _COLOR_BGR, _BORDER_THICK)

    def _draw_label(
        self,
        frame:     np.ndarray,
        text:      str,
        tl:        tuple[int, int],
        br:        tuple[int, int],
    ) -> None:
        """Nome da zona centrado dentro do retângulo."""
        (tw, th), _ = cv2.getTextSize(text, _FONT, _FONT_SCALE, _FONT_THICK)
        cx = (tl[0] + br[0]) // 2
        cy = (tl[1] + br[1]) // 2
        org = (cx - tw // 2, cy + th // 2)
        cv2.putText(frame, text, org, _FONT, _FONT_SCALE, _COLOR_BGR, _FONT_THICK)
