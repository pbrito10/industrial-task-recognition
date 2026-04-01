from __future__ import annotations

import cv2
import numpy as np


class Camera:
    """Abstração sobre cv2.VideoCapture para isolar o resto do sistema do OpenCV.

    Abre a câmera no construtor e expõe apenas o que o sistema precisa:
    ler frames, consultar FPS e libertar o recurso.
    """

    def __init__(self, index: int, width: int, height: int) -> None:
        self._capture = cv2.VideoCapture(index)
        # Configurar resolução pedida — a câmera pode não suportar e ajusta automaticamente
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        # Desativar autofoco — evita que a câmera perca o foco quando as mãos saem da cena
        self._capture.set(cv2.CAP_PROP_AUTOFOCUS, 0)

    def read_frame(self) -> np.ndarray | None:
        """Lê o próximo frame. Devolve None se a câmera falhou ou terminou."""
        success, frame = self._capture.read()
        if not success:
            return None
        return frame

    def fps(self) -> float:
        """FPS reportado pela câmera — usado para cálculos temporais no pipeline."""
        return self._capture.get(cv2.CAP_PROP_FPS)

    def is_open(self) -> bool:
        return self._capture.isOpened()

    def release(self) -> None:
        """Liberta o recurso — deve ser chamado no finally de quem usa a câmera."""
        self._capture.release()
