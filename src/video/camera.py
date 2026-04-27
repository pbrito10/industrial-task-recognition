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

        # Mapas pré-calculados para undistortion eficiente por frame (initUndistortRectifyMap)
        # Calculados uma vez no construtor; remap() aplica-os sem recalcular a cada frame
        self._undistort_maps = self._load_lens_calibration(calibration_path, width, height)

        self._flip = flip

        # Matriz de perspetiva para correção de vista (bird's-eye view)
        self._perspective_M, self._perspective_size = self._load_perspective_calibration(perspective_path)

    @classmethod
    def from_config(cls, config: dict) -> "Camera":
        """Constrói uma Camera a partir do dicionário camera: do settings.yaml."""
        return cls(
            index=config["index"],
            width=config["width"],
            height=config["height"],
            calibration_path=config.get("calibration_path"),
            perspective_path=config.get("perspective_path"),
            flip=config.get("flip", False),
        )

    def read_frame(self) -> np.ndarray | None:
        """Lê o próximo frame, aplicando correções de lente e perspetiva se disponíveis.
        Devolve None se a câmara falhou ou terminou."""
        success, frame = self._capture.read()
        if not success:
            return None
        # Lente → flip → perspetiva (ordem importante para calibração consistente)
        if self._undistort_maps is not None:
            frame = cv2.remap(frame, *self._undistort_maps, cv2.INTER_LINEAR)
        if self._flip:
            frame = cv2.flip(frame, -1)
        if self._perspective_M is not None:
            frame = cv2.warpPerspective(frame, self._perspective_M, self._perspective_size)
        return frame

    def _load_lens_calibration(
        self,
        calibration_path: str | None,
        width: int,
        height: int,
    ) -> tuple[np.ndarray, np.ndarray] | None:
        if not calibration_path:
            return None

        path = Path(calibration_path)
        if not path.exists():
            return None

        data = np.load(str(path))
        K, dist = data["K"], data["dist"]
        # newcameramtx guardado pelo calibrate_lens atual; fallback para K em ficheiros antigos
        newcameramtx = data["newcameramtx"] if "newcameramtx" in data else K
        return cv2.initUndistortRectifyMap(
            K, dist, None, newcameramtx, (width, height), cv2.CV_32FC1
        )

    def _load_perspective_calibration(
        self,
        perspective_path: str | None,
    ) -> tuple[np.ndarray | None, tuple[int, int] | None]:
        if not perspective_path:
            return None, None

        path = Path(perspective_path)
        if not path.exists():
            return None, None

        data = np.load(str(path))
        return data["M"], tuple(data["output_size"].tolist())

    def fps(self) -> float:
        """FPS reportado pela câmara — usado para cálculos temporais no pipeline."""
        return self._capture.get(cv2.CAP_PROP_FPS)

    def is_open(self) -> bool:
        """Verifica se a câmara está aberta e disponível para leitura."""
        return self._capture.isOpened()

    def release(self) -> None:
        """Liberta o recurso — deve ser chamado no finally de quem usa a câmara."""
        self._capture.release()
