from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


class Camera:
    """Abstração sobre cv2.VideoCapture para isolar o resto do sistema do OpenCV.

    Abre a câmara no construtor e expõe apenas o que o sistema precisa:
    ler frames, consultar FPS e libertar o recurso.
    """

    def __init__(self, index: int, width: int, height: int,
                 calibration_path: str | None = None,
                 perspective_path: str | None = None,
                 flip: bool = False) -> None:
        """Abre a câmara e configura a resolução pedida.
        :param index: int - índice da câmara (0 para a câmara padrão)
        :param width: int - largura de captura desejada em píxeis
        :param height: int - altura de captura desejada em píxeis
        :param calibration_path: caminho para o .npz de lente; None desativa
        :param perspective_path: caminho para o .npz de perspetiva; None desativa
        :param flip: True para rodar 180° (flip horizontal + vertical)
        """
        self._capture = cv2.VideoCapture(index)
        # Configurar resolução pedida — a câmara pode não suportar e ajusta automaticamente
        self._capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Parâmetros intrínsecos para correção de distorção de lente
        self._K: np.ndarray | None = None
        self._dist: np.ndarray | None = None
        if calibration_path:
            path = Path(calibration_path)
            if path.exists():
                data = np.load(str(path))
                self._K, self._dist = data["K"], data["dist"]

        self._flip = flip

        # Matriz de perspetiva para correção de vista (bird's-eye view)
        self._perspective_M: np.ndarray | None = None
        self._perspective_size: tuple[int, int] | None = None
        if perspective_path:
            path = Path(perspective_path)
            if path.exists():
                data = np.load(str(path))
                self._perspective_M = data["M"]
                self._perspective_size = tuple(data["output_size"].tolist())

    def read_frame(self) -> np.ndarray | None:
        """Lê o próximo frame, aplicando correções de lente e perspetiva se disponíveis.
        Devolve None se a câmara falhou ou terminou."""
        success, frame = self._capture.read()
        if not success:
            return None
        # Lente → flip → perspetiva (ordem importante para calibração consistente)
        if self._K is not None:
            frame = cv2.undistort(frame, self._K, self._dist)
        if self._flip:
            frame = cv2.flip(frame, -1)
        if self._perspective_M is not None:
            frame = cv2.warpPerspective(frame, self._perspective_M, self._perspective_size)
        return frame

    def fps(self) -> float:
        """FPS reportado pela câmara — usado para cálculos temporais no pipeline."""
        return self._capture.get(cv2.CAP_PROP_FPS)

    def is_open(self) -> bool:
        """Verifica se a câmara está aberta e disponível para leitura."""
        return self._capture.isOpened()

    def release(self) -> None:
        """Liberta o recurso — deve ser chamado no finally de quem usa a câmara."""
        self._capture.release()
