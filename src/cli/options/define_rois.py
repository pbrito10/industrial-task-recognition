from __future__ import annotations

from pathlib import Path
from typing import Callable

from src.roi.json_roi_repository import JsonRoiRepository
from src.roi.roi_drawer import RoiDrawer
from src.roi.roi_repository import RoiRepository
from src.video.camera import Camera


class DefineRoisOption:
    """Opção de menu para desenhar e guardar as zonas de trabalho (ROIs).

    Carrega ROIs existentes, abre o RoiDrawer e guarda o resultado.
    Se o utilizador sair sem guardar, as ROIs anteriores mantêm-se.

    3 variáveis de instância — exceção justificada pela natureza da opção:
    câmara, nomes das zonas e repositório são dependências independentes.
    """

    def __init__(
        self,
        camera_factory: Callable[[], Camera],
        zone_names: list[str],
        repository: RoiRepository,
    ) -> None:
        self._camera_factory = camera_factory
        self._zone_names = zone_names
        self._repository = repository

    @property
    def name(self) -> str:
        return "Definir ROIs"

    def run(self) -> None:
        existing = self._repository.load()

        drawer = RoiDrawer(
            camera_factory=self._camera_factory,
            zone_names=self._zone_names,
        )

        result = drawer.draw(existing)
        if result is None:
            print("Saiu sem guardar — ROIs anteriores mantidas.")
            return

        self._repository.save(result)
        print(f"ROIs guardadas: {len(result.all())} zonas definidas.")


def make_define_rois_option(
    config: dict,
    camera_factory: Callable[[], Camera],
) -> DefineRoisOption:
    """Factory que constrói DefineRoisOption a partir do dict do settings.yaml."""
    return DefineRoisOption(
        camera_factory=camera_factory,
        zone_names=config["tracking"]["cycle_zone_order"],
        repository=JsonRoiRepository(
            path=Path(__file__).parents[3] / "config" / "rois.json"
        ),
    )
