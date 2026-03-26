from __future__ import annotations

import time
from typing import Callable

import cv2
import numpy as np

from src.detection.detector_interface import DetectorInterface
from src.detection.hand_detection import HandDetection
from src.detection.mediapipe_detector import MediapipeDetector
from src.shared.hand_side import HandSide
from src.video.camera import Camera

# Ligações entre landmarks que formam o esqueleto da mão (convenção MediaPipe)
_HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Polegar
    (0, 5), (5, 6), (6, 7), (7, 8),        # Indicador
    (0, 9), (9, 10), (10, 11), (11, 12),   # Médio
    (0, 13), (13, 14), (14, 15), (15, 16), # Anelar
    (0, 17), (17, 18), (18, 19), (19, 20), # Mindinho
    (5, 9), (9, 13), (13, 17),             # Palma
]

# Cores por lado da mão em BGR
_HAND_COLORS: dict[HandSide, tuple[int, int, int]] = {
    HandSide.LEFT: (255, 100, 0),
    HandSide.RIGHT: (0, 200, 50),
}

# Constantes de desenho
_LINE_THICKNESS = 2
_KEYPOINT_RADIUS = 4
_LABEL_FONT_SCALE = 0.5
_OVERLAY_FONT_SCALE = 0.6
_FONT_THICKNESS = 1
_WINDOW_NAME = "Teste de Camara  |  q para sair"
_FONT = cv2.FONT_HERSHEY_SIMPLEX


class TestCameraOption:
    """Opção de menu que abre a câmara e mostra o feed com keypoints das mãos.

    Recebe factories em vez de instâncias — cria e liberta Camera e Detector
    em cada run(), garantindo recursos limpos independentemente de quantas
    vezes a opção for executada. (DIP: depende de abstrações, não concretos)
    """

    def __init__(
        self,
        camera_factory: Callable[[], Camera],
        detector_factory: Callable[[], DetectorInterface],
    ) -> None:
        self._camera_factory = camera_factory
        self._detector_factory = detector_factory

    @property
    def name(self) -> str:
        return "Testar camara"

    def run(self) -> None:
        """Cria os recursos, corre o loop e liberta tudo no finally."""
        camera = self._camera_factory()
        detector = self._detector_factory()

        # Pré-criar a janela para evitar múltiplas janelas em Wayland/Linux
        cv2.namedWindow(_WINDOW_NAME, cv2.WINDOW_NORMAL)

        try:
            self._run_loop(camera, detector)
        finally:
            camera.release()
            detector.release()
            cv2.destroyAllWindows()

    def _run_loop(self, camera: Camera, detector: DetectorInterface) -> None:
        prev_time = time.perf_counter()

        while True:
            annotated_frame, fps, prev_time = self._process_frame(camera, detector, prev_time)
            if annotated_frame is None:
                break
            cv2.imshow(_WINDOW_NAME, annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    def _process_frame(
        self,
        camera: Camera,
        detector: DetectorInterface,
        prev_time: float,
    ) -> tuple[np.ndarray | None, float, float]:
        """Lê, processa e anota um frame. Devolve None se a câmara falhou."""
        frame = camera.read_frame()
        if frame is None:
            print("Câmara indisponível.")
            return None, 0.0, prev_time

        detections = detector.detect(frame)
        self._draw_detections(frame, detections)

        now = time.perf_counter()
        fps = 1.0 / (now - prev_time) if now != prev_time else 0.0
        self._draw_overlay(frame, fps)

        return frame, fps, now

    def _draw_detections(
        self, frame: np.ndarray, detections: list[HandDetection]
    ) -> None:
        for detection in detections:
            self._draw_hand(frame, detection)

    def _draw_hand(self, frame: np.ndarray, detection: HandDetection) -> None:
        """Desenha esqueleto, keypoints e bounding box de uma mão."""
        color = _HAND_COLORS[detection.hand_side]
        keypoints = detection.keypoints

        for start_idx, end_idx in _HAND_CONNECTIONS:
            start = keypoints.by_index(start_idx).position
            end = keypoints.by_index(end_idx).position
            cv2.line(frame, (start.x, start.y), (end.x, end.y), color, _LINE_THICKNESS)

        for kp in keypoints.all():
            cv2.circle(frame, (kp.position.x, kp.position.y), _KEYPOINT_RADIUS, color, -1)

        tl = detection.bounding_box.top_left
        br = detection.bounding_box.bottom_right
        cv2.rectangle(frame, (tl.x, tl.y), (br.x, br.y), color, _LINE_THICKNESS)

        label = f"{detection.hand_side.value}  {detection.confidence.as_percentage():.0f}%"
        cv2.putText(frame, label, (tl.x, tl.y - 8), _FONT, _LABEL_FONT_SCALE, color, _FONT_THICKNESS)

    def _draw_overlay(self, frame: np.ndarray, fps: float) -> None:
        """Mostra FPS e resolução no canto superior esquerdo."""
        h, w = frame.shape[:2]
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 25), _FONT, _OVERLAY_FONT_SCALE, (255, 255, 255), _FONT_THICKNESS)
        cv2.putText(frame, f"{w}x{h}", (10, 50), _FONT, _OVERLAY_FONT_SCALE, (255, 255, 255), _FONT_THICKNESS)


def make_test_camera_option(
    config: dict,
    camera_factory: Callable[[], Camera],
) -> TestCameraOption:
    """Factory que constrói TestCameraOption a partir do dict do settings.yaml.

    O detector_factory fica aqui encapsulado — main.py não precisa de saber
    que existe um MediapipeDetector.
    """
    def detector_factory() -> DetectorInterface:
        return MediapipeDetector(
            model_path=config["detection"]["model_path"],
            max_num_hands=config["detection"]["max_num_hands"],
            min_detection_confidence=config["detection"]["min_detection_confidence"],
            min_tracking_confidence=config["detection"]["min_tracking_confidence"],
        )

    return TestCameraOption(
        camera_factory=camera_factory,
        detector_factory=detector_factory,
    )
