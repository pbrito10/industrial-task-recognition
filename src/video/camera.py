from __future__ import annotations

import cv2
import numpy as np


class Camera:
    """Abstração sobre cv2.VideoCapture para isolar o resto do sistema do OpenCV.

    Abre a câmara no construtor e expõe apenas o que o sistema precisa:
    ler frames, consultar FPS e libertar o recurso.
    """

    def __init__(self, index: int, width: int, height: int) -> None:
        self._capture = cv2.VideoCapture(index)
        # Configurar resolução pedida — a câmara pode não suportar e ajusta automaticamente
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def read_frame(self) -> np.ndarray | None:
        """Lê o próximo frame. Devolve None se a câmara falhou ou terminou."""
        success, frame = self._capture.read()
        if not success:
            return None
        return frame

    def fps(self) -> float:
        """FPS reportado pela câmara — usado para cálculos temporais no pipeline."""
        return self._capture.get(cv2.CAP_PROP_FPS)

    def is_open(self) -> bool:
        return self._capture.isOpened()

    def release(self) -> None:
        """Liberta o recurso — deve ser chamado no finally de quem usa a câmara."""
        self._capture.release()
