# Ponto de entrada da aplicação — equivalente ao main() em C/Java.
# Responsabilidade: carregar configuração, construir dependências e arrancar o menu.

from pathlib import Path

import yaml

from src.cli.menu import Menu
from src.cli.options.define_rois import make_define_rois_option
from src.cli.options.test_camera import make_test_camera_option
from src.video.camera import Camera

_CONFIG_PATH = Path(__file__).parent / "config" / "settings.yaml"


def main() -> None:
    with open(_CONFIG_PATH, "r") as config_file:
        config = yaml.safe_load(config_file)

    # Única dependência partilhada entre opções — fica no composition root
    camera_factory = lambda: Camera(
        index=config["camera"]["index"],
        width=config["camera"]["width"],
        height=config["camera"]["height"],
    )

    Menu([
        make_test_camera_option(config, camera_factory),
        make_define_rois_option(config, camera_factory),
    ]).run()


if __name__ == "__main__":
    main()
