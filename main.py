# Ponto de entrada da aplicação — equivalente ao main() em C/Java.
# Responsabilidade: carregar configuração, construir dependências e arrancar o menu.

from pathlib import Path

import yaml

from src.cli.menu import Menu
from src.cli.options.test_camera import TestCameraOption
from src.detection.mediapipe_detector import MediapipeDetector
from src.video.camera import Camera

_CONFIG_PATH = Path(__file__).parent / "config" / "settings.yaml"


def main() -> None:
    with open(_CONFIG_PATH, "r") as config_file:
        config = yaml.safe_load(config_file)

    options = [
        TestCameraOption(
            camera_factory=lambda: Camera(
                index=config["camera"]["index"],
                width=config["camera"]["width"],
                height=config["camera"]["height"],
            ),
            detector_factory=lambda: MediapipeDetector(
                model_path=config["detection"]["model_path"],
                max_num_hands=config["detection"]["max_num_hands"],
                min_detection_confidence=config["detection"]["min_detection_confidence"],
                min_tracking_confidence=config["detection"]["min_tracking_confidence"],
            ),
        ),
        # Definir ROIs e Correr programa — a implementar nas próximas iterações
    ]

    Menu(options).run()


if __name__ == "__main__":
    main()
